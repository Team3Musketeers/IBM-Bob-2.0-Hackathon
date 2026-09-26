"""Validate synthesis output and render it into the dashboard dataset.

    dataset/audit*.json  ->  dashboard/static/dashboard_data.json

This script does **not** compute Communication Debt Scores. Scoring is
owned by the synthesis step specified in `prompts/synthesis.md`; this
only checks that a synthesis run is internally consistent and reshapes it
for display. Two runs of the same PR must never be silently merged or
silently preferred -- disagreements between them are reported.

Input shapes, both accepted:

* v1 - ``dataset/audit_results.json``: an array of records, each with
  ``pr_number``, bare-string ``predicted_questions``, no consensus fields.
* v2 - ``dataset/audit_<N>_v2.json``: a single record with no
  ``pr_number`` (inferred from the filename), ``predicted_questions`` as
  ``{question, file, line}`` objects, plus ``agent_consensus``,
  ``human_review_recommended`` and ``disagreement_note``.

Validation is strict on purpose. A synthesis run that disagrees with
itself is a bug worth failing on, not a dashboard to render.

Usage::

    python dashboard/render_dashboard.py           # write the dataset
    python dashboard/render_dashboard.py --check   # validate only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIRS = (REPO_ROOT / "dataset", REPO_ROOT / "data" / "dataset")
RESULT_GLOB = "audit*.json"
OUTPUT = Path(__file__).resolve().parent / "static" / "dashboard_data.json"

REQUIRED_KEYS = ("true_summary", "undisclosed_changes", "scope_flags", "predicted_questions")
SCORE_COMPONENTS = ("description_gap", "scope_creep", "unanswered_risk")
CONSENSUS_VALUES = ("aligned", "partial", "diverged")

BAND_LOW_MAX = 25
BAND_MEDIUM_MAX = 45

PR_IN_FILENAME = re.compile(r"(\d{4,6})")
CHECKLIST_LINE = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s*")
CHECKLIST_HEADER = re.compile(r"^\s*#{0,6}\s*checklist\s*:?\s*$", re.IGNORECASE)
MARKDOWN_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
GUIDE_LINK = re.compile(r"^\s*\[(contribution guidelines|how to open a pull request guide)\]", re.IGNORECASE)
CLOSES_TICKET = re.compile(r"\b(?:closes|fixes|resolves)\s+#(\d+)", re.IGNORECASE)


class ValidationError(Exception):
    """Raised when a synthesis run cannot be trusted."""


def dataset_dir() -> Path:
    for candidate in DATASET_DIRS:
        if candidate.is_dir():
            return candidate
    raise ValidationError(f"no dataset directory found; looked in {DATASET_DIRS}")


def read_json(path: Path) -> object:
    encoding = "utf-16" if path.suffix == ".json" and _looks_utf16(path) else "utf-8"
    try:
        with path.open(encoding=encoding) as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path.name}: unreadable ({exc})") from exc


def _looks_utf16(path: Path) -> bool:
    with path.open("rb") as handle:
        return handle.read(2) in (b"\xff\xfe", b"\xfe\xff")


def load_records(directory: Path) -> list[dict]:
    """Collect every synthesis record, tagging each with its source file."""
    records: list[dict] = []
    seen_files: set[str] = set()
    for path in sorted(directory.glob(RESULT_GLOB)):
        payload = read_json(path)
        batch = payload if isinstance(payload, list) else [payload]
        for record in batch:
            if not isinstance(record, dict):
                raise ValidationError(f"{path.name}: expected an object, got {type(record).__name__}")
            if REQUIRED_KEYS[0] not in record:
                continue
            number = record.get("pr_number")
            if not isinstance(number, int):
                found = PR_IN_FILENAME.search(path.stem)
                if not found:
                    raise ValidationError(f"{path.name}: no pr_number and none inferable from filename")
                number = int(found.group(1))
            records.append({**record, "pr_number": number, "_source": path.name})
            seen_files.add(path.name)
    if not records:
        raise ValidationError(f"no synthesis records found in {directory} (glob {RESULT_GLOB})")
    return records


def resolve_duplicates(records: list[dict]) -> tuple[list[dict], list[str]]:
    """Keep one record per PR, preferring the richer schema. Report the rest."""
    warnings: list[str] = []
    chosen: dict[int, dict] = {}
    for record in records:
        number = record["pr_number"]
        current = chosen.get(number)
        if current is None:
            chosen[number] = record
            continue
        keep, drop = (record, current) if _richness(record) > _richness(current) else (current, record)
        if keep["communication_debt_score"] != drop.get("communication_debt_score"):
            warnings.append(
                f"PR #{number}: {keep['_source']} scores {keep['communication_debt_score']} "
                f"but {drop['_source']} scores {drop.get('communication_debt_score')}; "
                f"kept {keep['_source']}"
            )
        elif drop["_source"] != keep["_source"]:
            warnings.append(f"PR #{number}: {drop['_source']} superseded by {keep['_source']} (equal scores)")
        chosen[number] = keep
    return [chosen[n] for n in sorted(chosen)], warnings


def _richness(record: dict) -> int:
    return sum(
        [
            "agent_consensus" in record,
            isinstance(record.get("predicted_questions"), list)
            and bool(record["predicted_questions"])
            and isinstance(record["predicted_questions"][0], dict),
        ]
    )


def strip_contribution_checklist(body: str) -> str:
    """Reduce a freeCodeCamp PR body to the author's actual claim.

    Every body opens with the same contribution checklist, which buries
    the claim the audit is comparing against.
    """
    body = MARKDOWN_COMMENT.sub("", body)
    kept: list[str] = []
    in_checklist = False
    for line in body.splitlines():
        if CHECKLIST_HEADER.match(line) or CHECKLIST_LINE.match(line):
            in_checklist = True
            continue
        if in_checklist and (not line.strip() or GUIDE_LINK.match(line)):
            continue
        if in_checklist and line.strip():
            in_checklist = False
        if line.strip():
            kept.append(line.rstrip())
    return "\n".join(kept).strip()


def normalise_questions(raw: object, pr_number: int) -> list[dict]:
    """Accept bare strings (v1) and {question, file, line} objects (v2)."""
    if not isinstance(raw, list):
        raise ValidationError(f"PR #{pr_number}: predicted_questions must be a list")
    out: list[dict] = []
    for item in raw:
        if isinstance(item, str):
            if not item.strip():
                raise ValidationError(f"PR #{pr_number}: empty predicted question")
            out.append({"question": item.strip(), "file": None, "line": None})
        elif isinstance(item, dict) and str(item.get("question", "")).strip():
            out.append(
                {
                    "question": str(item["question"]).strip(),
                    "file": item.get("file") or None,
                    "line": str(item.get("line")) if item.get("line") is not None else None,
                }
            )
        else:
            raise ValidationError(f"PR #{pr_number}: unrecognised predicted question {item!r}")
    return out


def normalise_flags(raw: object, pr_number: int) -> list[dict]:
    if not isinstance(raw, list):
        raise ValidationError(f"PR #{pr_number}: scope_flags must be a list")
    out: list[dict] = []
    for flag in raw:
        if isinstance(flag, str) and flag.strip():
            out.append({"type": "unspecified", "detail": flag.strip()})
        elif isinstance(flag, dict) and str(flag.get("detail", "")).strip():
            out.append(
                {
                    "type": str(flag.get("type", "unspecified")).strip(),
                    "detail": str(flag["detail"]).strip(),
                }
            )
        else:
            raise ValidationError(f"PR #{pr_number}: unrecognised scope flag {flag!r}")
    return out


def score_band(score: int) -> str:
    if score < BAND_LOW_MAX:
        return "low"
    return "medium" if score <= BAND_MEDIUM_MAX else "high"


def load_meta(pr_number: int) -> dict:
    for directory in DATASET_DIRS:
        path = directory / f"pr_{pr_number}_meta.json"
        if path.is_file():
            meta = read_json(path)
            if not isinstance(meta, dict):
                raise ValidationError(f"PR #{pr_number}: metadata is not an object")
            if meta.get("number") not in (None, pr_number):
                raise ValidationError(f"PR #{pr_number}: metadata declares number {meta.get('number')!r}")
            return meta
    raise ValidationError(f"PR #{pr_number}: no metadata found in {[str(d) for d in DATASET_DIRS]}")


def build_entry(record: dict) -> dict:
    number = record["pr_number"]
    missing = [key for key in REQUIRED_KEYS if key not in record]
    if missing:
        raise ValidationError(f"PR #{number} ({record['_source']}): missing {missing}")

    score = record.get("communication_debt_score")
    if not isinstance(score, int) or not 0 <= score <= 100:
        raise ValidationError(f"PR #{number} ({record['_source']}): score must be an int 0-100, got {score!r}")

    breakdown = record.get("score_breakdown")
    if not isinstance(breakdown, dict):
        raise ValidationError(f"PR #{number} ({record['_source']}): missing score_breakdown")
    absent = [key for key in SCORE_COMPONENTS if not isinstance(breakdown.get(key), int)]
    if absent:
        raise ValidationError(f"PR #{number} ({record['_source']}): score_breakdown missing {absent}")
    unexpected = set(breakdown) - set(SCORE_COMPONENTS)
    if unexpected:
        raise ValidationError(f"PR #{number} ({record['_source']}): unexpected breakdown keys {sorted(unexpected)}")
    total = sum(breakdown[key] for key in SCORE_COMPONENTS)
    if total != score:
        raise ValidationError(
            f"PR #{number} ({record['_source']}): score_breakdown sums to {total} "
            f"but communication_debt_score is {score}"
        )

    consensus = record.get("agent_consensus")
    if consensus is not None and consensus not in CONSENSUS_VALUES:
        raise ValidationError(f"PR #{number}: agent_consensus must be one of {CONSENSUS_VALUES}, got {consensus!r}")

    undisclosed = record["undisclosed_changes"]
    if not isinstance(undisclosed, list):
        raise ValidationError(f"PR #{number}: undisclosed_changes must be a list")
    questions = normalise_questions(record["predicted_questions"], number)
    flags = normalise_flags(record["scope_flags"], number)

    meta = load_meta(number)
    body = meta.get("body", "") or ""
    claim = strip_contribution_checklist(body)

    linked = record.get("ticket_linked")
    if isinstance(linked, bool):
        ticket, ticket_source = linked, "synthesis"
    else:
        match = CLOSES_TICKET.search(body)
        ticket, ticket_source = (bool(match), "derived from description") if match else (False, "none found")

    diffstat = [
        label
        for label in (
            f"{meta.get('changedFiles')} files" if meta.get("changedFiles") is not None else None,
            f"+{meta['additions']}" if meta.get("additions") is not None else None,
            f"-{meta['deletions']}" if meta.get("deletions") is not None else None,
        )
        if label
    ]

    entry = {
        "pr_number": number,
        "url": meta.get("url") or f"https://github.com/freeCodeCamp/freeCodeCamp/pull/{number}",
        "title": meta.get("title") or f"PR #{number}",
        "diffstat": " · ".join(diffstat),
        "author_claim": claim,
        "communication_debt_score": score,
        "score_band": score_band(score),
        "score_breakdown": {key: breakdown[key] for key in SCORE_COMPONENTS},
        "subagent_a": {
            "slug": "technical-truth-teller",
            "true_summary": record["true_summary"],
            "undisclosed_changes": [str(item) for item in undisclosed],
        },
        "subagent_b": {
            "slug": "scope-auditor",
            "ticket_linked": ticket,
            "ticket_source": ticket_source,
            "scope_flags": flags,
        },
        "subagent_c": {"slug": "reviewers-ghost", "predicted_questions": questions},
        "totals": {
            "undisclosed_changes": len(undisclosed),
            "scope_flags": len(flags),
            "predicted_questions": len(questions),
        },
        "source_file": record["_source"],
    }
    if consensus is not None:
        entry["agent_consensus"] = consensus
    if "human_review_recommended" in record:
        entry["human_review_recommended"] = bool(record["human_review_recommended"])
    if record.get("disagreement_note"):
        entry["disagreement_note"] = str(record["disagreement_note"])
    for passthrough in ("_note",):
        if passthrough in record:
            entry[passthrough] = record[passthrough]
    return entry


def summarise(entries: list[dict]) -> dict:
    scores = [entry["communication_debt_score"] for entry in entries]
    consensus: dict[str, int] = {}
    for entry in entries:
        key = entry.get("agent_consensus", "not recorded")
        consensus[key] = consensus.get(key, 0) + 1
    return {
        "prs_audited": len(entries),
        "total_undisclosed_changes": sum(e["totals"]["undisclosed_changes"] for e in entries),
        "total_scope_flags": sum(e["totals"]["scope_flags"] for e in entries),
        "total_predicted_questions": sum(e["totals"]["predicted_questions"] for e in entries),
        "mean_score": round(sum(scores) / len(scores), 1),
        "max_score": max(scores),
        "min_score": min(scores),
        "human_review_recommended": sum(1 for e in entries if e.get("human_review_recommended")),
        "agent_consensus": consensus,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="validate only; write nothing")
    parser.add_argument(
        "--allow-score-conflicts",
        action="store_true",
        help="warn instead of failing when two files disagree on a PR's score",
    )
    args = parser.parse_args()

    try:
        directory = dataset_dir()
        records = load_records(directory)
        entries, warnings = resolve_duplicates(records)
        payload_entries = [build_entry(record) for record in entries]
    except ValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    blocking = [w for w in warnings if "scores" in w and "superseded" not in w]
    if blocking and not args.allow_score_conflicts:
        print(
            "error: synthesis runs disagree on the same PR. Reconcile them, or pass "
            "--allow-score-conflicts to publish the richer run and surface the conflict in the UI.",
            file=sys.stderr,
        )
        return 1

    payload_entries.sort(key=lambda e: (-e["communication_debt_score"], e["pr_number"]))
    payload = {
        "_generated_by": "dashboard/render_dashboard.py",
        "_source": "dataset/audit*.json (synthesis output per prompts/synthesis.md)",
        "_notes": warnings,
        "bands": {"low": f"< {BAND_LOW_MAX}", "medium": f"{BAND_LOW_MAX}-{BAND_MEDIUM_MAX}", "high": f"> {BAND_MEDIUM_MAX}"},
        "summary": summarise(payload_entries),
        "prs": payload_entries,
    }

    if args.check:
        if not OUTPUT.is_file():
            print(f"error: {OUTPUT} not found; run without --check", file=sys.stderr)
            return 1
        if read_json(OUTPUT) != payload:
            print(f"error: {OUTPUT.name} is stale; run `python dashboard/render_dashboard.py`", file=sys.stderr)
            return 1
        print(f"ok: {len(payload_entries)} PRs validated, dashboard data up to date")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    stats = payload["summary"]
    print(
        f"wrote {OUTPUT.relative_to(REPO_ROOT)}: {stats['prs_audited']} PRs, "
        f"mean {stats['mean_score']}, range {stats['min_score']}-{stats['max_score']}, "
        f"{stats['human_review_recommended']} flagged for human review"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
