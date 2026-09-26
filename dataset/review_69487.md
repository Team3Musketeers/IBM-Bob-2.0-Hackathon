## 👻 Ghostwriter Review

**Communication Debt: 52/100 — Significant**

### What actually changed
- `PaypalButton` and the deleted `PayPalButtonScriptLoader` class (204 lines) are replaced with a function component backed by `@paypal/react-paypal-js@10.3.0` — new dependency added to `package.json` and lock file.
- `donate-form.tsx` drops the `isPaypalLoading` prop pass-through; `paypal-button.tsx` also removes the `isSubscription` and `ref?` props from `PaypalButtonProps`, deriving subscription state internally.
- `intent: 'CAPTURE'` is now explicitly passed in `createOrder` — absent in the old implementation.
- The E2E fake-PayPal SDK (`paypal-donation.spec.ts`) is simplified: `Buttons.driver(...)` shim removed, `isEligible` and a `Promise.resolve()` return added.

### Undisclosed changes
- `isPaypalLoading` prop deleted from `PaypalButtonProps` and `donate-form.tsx` — component API break, not mentioned.
- `isSubscription` and `ref?` props silently removed from `PaypalButtonProps`.
- `defaultDonation` import dropped; `amount`/`duration`/`planId` now re-derived from props on every render.
- `intent: 'CAPTURE'` newly explicit in `createOrder` — no mention of whether its absence was previously causing capture-flow issues.
- `server-only`, `promise-polyfill`, `hi-base32` added as transitive deps; not discussed.
- 7-line E2E comment block explaining the legacy `Buttons.driver` API deleted — loses historical context.

### Review before merge
- [ ] Confirm how the loading/skeleton UX previously driven by `isPaypalLoading` is now surfaced to the parent, or confirm it was intentionally dropped.
- [ ] Verify that `optionsKey` changing (e.g. on one-time ↔ monthly toggle) does not cause a visible SDK reload flicker in production.
- [ ] Confirm `intent: 'CAPTURE'` is correct and harmless relative to the old implicit behaviour.
- [ ] Confirm Gatsby's SSR pipeline handles the `server-only` transitive dep without a build failure.