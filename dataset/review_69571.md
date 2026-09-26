## 👻 Ghostwriter Review

**Communication Debt: 28/100 — Moderate**

### What actually changed
- `FaqItem` in [`donation-text-components.tsx`](client/src/components/Donation/donation-text-components.tsx) is converted from a plain function called imperatively to a proper JSX component, with `key` renamed to `index` and a stable `contentId` derived from it.
- Each FAQ button is now wrapped in an `<h3 className='faq-question-heading'>` — an accessibility improvement beyond what the issue prescribed.
- `.faq-question-heading { margin: 0 }` added to [`donation.css`](client/src/components/Donation/donation.css).
- New test file [`donation-text-components.test.tsx`](client/src/components/Donation/donation-text-components.test.tsx) adds 3 tests covering heading structure, independent expand/collapse, and no hook-rule violations.

### Undisclosed changes
- `<h3>` semantic wrapper added — not mentioned in the description; changes DOM structure and may break existing CSS selectors targeting `.faq-item > button` directly.
- CSS rule addition (`.faq-question-heading { margin: 0 }`) not mentioned.
- Test file addition not mentioned.

### Review before merge
- [ ] Confirm no existing CSS rules target `.faq-item > button` or `.faq-item .map-title` directly — the new `<h3>` wrapper breaks those selectors. Run a visual check on the FAQ layout.
- [ ] Consider replacing `fireEvent.click` with `@testing-library/user-event`'s `userEvent.click` for more realistic event simulation — requires adding the `userEvent` import and making the affected test callbacks `async`, so left as a manual follow-up rather than a one-line suggestion.

### Suggested fix

`aria-expanded` is set to a boolean in the diff — some assistive technology implementations expect the string form. In [`donation-text-components.tsx`](client/src/components/Donation/donation-text-components.tsx):

```suggestion
                    aria-expanded={isExpanded ? 'true' : 'false'}
```