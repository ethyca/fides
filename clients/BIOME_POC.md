# Biome PoC — ENG-3785

This branch replaces ESLint 8 + Prettier 3 with [Biome](https://biomejs.dev) 2.4.15 across every package in `clients/`. The goal is to evaluate Biome as a single replacement for the current FE lint + format stack, rather than upgrade ESLint to v9 and continue fighting Prettier in VS Code.

## TL;DR

- **CI is green.** `npm run check:ci` exits 0. No errors, 730 warnings (latent issues Biome surfaced that ESLint missed).
- **Massive simplification.** 19 config files → 1. ~75 devDeps removed. Lint + format are now one tool, run once at the repo root.
- **Lint runtime: 0.5s for 2,766 files** (Biome) vs minutes for ESLint + Prettier across the turbo fan-out.
- **No rule porting.** We use stock Biome `recommended` + the `react`, `next`, and `test` domains. The only rule edits are off/warn toggles for rules where the codebase has a documented historical opt-out (`noExplicitAny`, `noNonNullAssertion`) or where Biome surfaces enough net-new findings that a remediation pass is needed before they can block CI.
- **Decision asked:** ship, ship with follow-up tickets for the 730 warnings, or abandon and pursue ESLint v9.

## What changed

| Before | After |
|---|---|
| ESLint 8.57 + Prettier 3.8.3 | Biome 2.4.15 |
| 6 `.eslintrc.cjs` + 5 `.prettierrc.json` + 5 `.prettierignore` + 3 nested `.eslintrc.cjs` (cypress/tests) = 19 config files | 1 `biome.json` at `clients/` root |
| `eslint`, `eslint-config-airbnb`, `eslint-config-airbnb-typescript`, `eslint-config-next`, `eslint-config-prettier`, `eslint-config-preact`, `eslint-plugin-cypress`, `eslint-plugin-import`, `eslint-plugin-jsdoc`, `eslint-plugin-jsx-a11y`, `eslint-plugin-no-only-tests`, `eslint-plugin-prettier`, `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-simple-import-sort`, `eslint-plugin-storybook`, `eslint-plugin-tailwindcss`, `@typescript-eslint/*`, `prettier`, `@types/eslint*` (~75 packages across 5 workspace packages) | `@biomejs/biome` only, single root install |
| turbo fans out `lint` + `format` per package | `biome ci .` runs once at root over the whole monorepo |
| lint-staged: `prettier --write` + `eslint --fix` | lint-staged: `biome check --write` |
| VS Code: Prettier extension + ESLint extension, `source.fixAll.eslint` on save | VS Code: Biome extension, `source.fixAll.biome` + `source.organizeImports.biome` on save |

## Configuration

`clients/biome.json`:

- `linter.rules.recommended: true` plus `domains: { react, next, test }`. The domains auto-enable react-hooks, Next.js (img element, html-link-for-pages, etc.), and test (`noFocusedTests` covers `.only`) rule sets.
- Two rules turned **off** to match prior policy: `noExplicitAny`, `noNonNullAssertion`. Both were eslint-disabled extensively in the prior codebase; no behavior change.
- Sixteen rules **downgraded** from error to warn to keep CI green while documenting net-new findings (see "Warnings outstanding" below).
- CSS files: `noUnknownAtRules` disabled (Tailwind `@tailwind` directives).
- Ignored paths mirror the prior `.prettierignore` and `.eslintignore` (generated API types, `.next/`, `dist/`, `public/lib/`, `public/scripts/`, fides-js GPP modules, demo HTML).

## Diff scope

- **Formatter pass (commit 1):** 60 files reformatted. Prettier 3.8.3's defaults are nearly identical to Biome's, so the formatter delta is tiny.
- **Safe-fix pass (commit 2):** 1,140 files modified. Mostly import organization (Biome merges duplicate sources, sorts named specifiers, and adds `type` keywords to type-only imports). No behavior changes. **Crucially, no React hook dependency arrays were modified** (Biome's `useExhaustiveDependencies` was downgraded to warn so the autofix didn't touch deps that were intentionally excluded in the previous code with `// eslint-disable-next-line react-hooks/exhaustive-deps`).
- **Scripts + tooling (commit 3):** 28 files. 19 config files deleted, 5 `package.json` files updated, `turbo.json` simplified, VS Code config swapped, lockfiles regenerated.

## Warnings outstanding (795 total)

Biome catches a strict superset of what the prior ESLint config caught. After applying every safe autofix, these latent issues remain. Each is downgraded from error to warn in `biome.json` so CI passes:

| Rule | Count | Notes |
|---|---:|---|
| `correctness/useExhaustiveDependencies` | 203 | React hook deps; many sites used `// eslint-disable react-hooks/exhaustive-deps` intentionally. Needs per-site review. |
| `correctness/noUnusedImports` | 135 | Auto-fixable with `--unsafe`; deferred. |
| `correctness/noUnusedFunctionParameters` | 115 | Often params kept for API signature compatibility; needs case-by-case review (prefix with `_` to silence). |
| `complexity/useOptionalChain` | 58 | Mechanical rewrite from `a && a.b` to `a?.b`. Can be batch-applied. |
| `correctness/noUnusedVariables` | 38 | Mostly safe to delete; some may be intentional. |
| `suspicious/useIterableCallbackReturn` | 35 | Likely real bugs (callbacks to `.find`/`.filter`/`.map` missing returns). |
| `suspicious/noImplicitAnyLet` | 33 | `let x;` → `let x: SomeType;`. Mechanical. |
| `a11y/noSvgWithoutTitle` | 23 | Add `<title>` to icon SVGs or `aria-hidden="true"` for decorative. Real a11y gap. |
| `suspicious/noArrayIndexKey` | 17 | React `key={i}`; some legit for static lists, most are issues. |
| `performance/noAccumulatingSpread` | 15 | `acc = [...acc, x]` in reduce. Real perf issue. |
| `a11y/noStaticElementInteractions` | 14 | `<div onClick>` should be `<button>` or have role + keyboard handler. |
| `style/noDescendingSpecificity` | 13 | CSS specificity issues. |
| `complexity/noBannedTypes` | 12 | `{}` / `Object` / `Function` types. |
| `style/useNodejsImportProtocol` | 12 (infos) | Use `node:fs` over `fs`. Trivial. |
| `suspicious/noNonNullAssertedOptionalChain` | 10 | `foo?.bar!` patterns; usually real bugs. |
| `suspicious/noConfusingVoidType` | 10 | `void` used outside return position. |
| `a11y/useSemanticElements` | 9 | `<div role="button">` should be `<button>`. |
| `suspicious/noShadowRestrictedNames` | 7 | Variables named `Promise`, `name`, `top`, etc. |
| `correctness/useHookAtTopLevel` | 6 | Hooks called conditionally. |
| `complexity/noUselessFragments` | 6 (infos) | `<>{x}</>` with single child. |
| `style/useTemplate` | 5 (infos) | String concatenation → template literal. |
| `suspicious/noDuplicateProperties` | 4 | CSS duplicate property declarations. Real bugs. |
| `complexity/noUselessSwitchCase` | 4 (infos) | |
| `security/noDangerouslySetInnerHtml` | 3 | Usually intentional for sanitized HTML; need per-site `// biome-ignore` with reason. |
| `performance/noImgElement` | 3 | Use Next.js `<Image>`. |
| `correctness/useJsxKeyInIterable` | 3 | Missing `key` on iterated JSX. Real bugs. |
| `complexity/noImportantStyles` | 3 | `!important` in CSS. |
| `a11y/noNoninteractiveTabindex` | 3 | `tabindex` on non-interactive element. |
| Rest | ~25 | Single-digit counts. |

### Why aren't these already clean?

Most of these rules **were already enabled** by `airbnb`, `airbnb-typescript`, `next/core-web-vitals`, and `jsx-a11y`. The codebase wasn't clean of them; the prior setup just didn't surface them as failures. Three reasons:

**1. Severity was `warn`, not `error`, in airbnb.** ESLint warnings didn't fail CI under the prior setup, so these accumulated silently:

| Biome rule (now) | ESLint rule (then) | Why it was silent |
|---|---|---|
| `noArrayIndexKey` (17) | `react/no-array-index-key` | airbnb: warn |
| `noDangerouslySetInnerHtml` (3) | `react/no-danger` | airbnb: warn |
| `noUselessFragments` (6) | `react/jsx-no-useless-fragment` | airbnb: warn |
| `noStaticElementInteractions` (14), `useSemanticElements` (9), `useKeyWithClickEvents` (2), `noNoninteractiveTabindex` (3), `useAriaPropsForRole` (2), most other a11y | `jsx-a11y/*` | jsx-a11y defaults: warn |

**2. 461 inline `eslint-disable` comments in source code.** Biome ignores them. The largest categories track exactly with what we now see:

| Biome rule (now) | ESLint rule disabled inline (then) |
|---|---|
| `useExhaustiveDependencies` (203) | `react-hooks/exhaustive-deps` |
| `useHookAtTopLevel` (6) | `react-hooks/rules-of-hooks` |
| `noUnusedImports` (135), `noUnusedVariables` (38), `noUnusedFunctionParameters` (115) | `@typescript-eslint/no-unused-vars` |

The 461 inline disables remain as dead text under Biome (they're inert). They can be deleted in a cleanup follow-up.

**3. Custom overrides in the prior config that Biome doesn't support.**

| Biome rule (now) | Prior ESLint config | Why it was silent |
|---|---|---|
| `noImgElement` (3) | `@next/next/no-img-element: "off"` in admin-ui | Explicitly turned off |
| `noLabelWithoutControl` (2) | `jsx-a11y/label-has-associated-control` with `depth: 25, assert: "either"` | Very permissive depth; Biome has no equivalent option |
| Various a11y on Ant Design components | `jsx-a11y` custom component map (`AutoComplete` → input, `Button` → button, etc.) | Biome doesn't support custom component mappings either way |

**Genuinely net-new** (no equivalent in the prior config, so ESLint never had a chance):

- `noImplicitAnyLet` (33) — `let x;` without type
- `noSvgWithoutTitle` (23) — a11y, no jsx-a11y equivalent
- `noAccumulatingSpread` (15) — perf
- `noConfusingVoidType` (10)
- `noDescendingSpecificity` (13), `noDuplicateProperties` (4), `noImportantStyles` (3) — CSS rules
- `useNodejsImportProtocol` (12) — `node:` protocol enforcement
- `noExportsInTest` (2)

**Implication for the remediation plan:** most of the work isn't "fix new things Biome added" — it's "stop pretending warn-level violations don't exist, and stop carrying inline-disable comments." After each follow-up remediation, the downgraded rules in `biome.json` can be re-promoted to `error`.

### Surgical `eslint-disable` → `biome-ignore` conversion (53 sites)

After the rule tuning, two passes converted `// eslint-disable-next-line <rule>` comments to `// biome-ignore lint/<biome-rule>: migrated from eslint-disable` — but **only** where the targeted ESLint rule maps 1:1 to a Biome rule **and** Biome is actually flagging the matching diagnostic. This avoids "unused suppression" warnings (Biome treats them as diagnostics themselves).

**Pass 1 (24 sites): generic.** For each disable, check the line immediately below for a matching Biome warning.

**Pass 2 (29 sites): react-hooks/exhaustive-deps.** This pattern needed its own pass because the disable comment sits inside the hook callback body (before the deps array), but Biome flags the `useEffect`/`useMemo`/`useCallback` call several lines above. The script scans up from each disable for the nearest hook call, confirms Biome is warning there, deletes the in-body comment, and inserts `// biome-ignore` immediately before the hook call.

Results:

| Biome rule | Warnings before | After | Re-promoted to error? |
|---|---:|---:|---|
| `useExhaustiveDependencies` | 203 | 153 | No (lots of net-new findings remain) |
| `noArrayIndexKey` | 17 | 1 | No (1 non-disabled site remains) |
| `useJsxKeyInIterable` | 3 | 0 | Yes |
| `noDangerouslySetInnerHtml` | 3 | 1 | No |
| `noImgElement` | 3 | 2 | No |
| `useHookAtTopLevel` | 6 | 5 | No |
| `noNoninteractiveTabindex` | 3 | 2 | No |

53 conversions total. Warnings: 795 → 730.

Of the 329 inline `eslint-disable-next-line` comments in source:
- **53** had a 1:1 mappable rule **and** a matching Biome warning — converted.
- **~116** had a 1:1 mappable rule but **no matching Biome warning** — left untouched (Biome's rule doesn't agree the line is a violation, or the disable was protecting against a different plugin's interpretation).
- **160** target rules Biome has no equivalent for (`global-require`, `cypress/no-unnecessary-waiting`, `tailwindcss/no-custom-classname`, `import/*`, `no-underscore-dangle`, `@typescript-eslint/naming-convention`, etc.) — left as dead text. Can be deleted in a cleanup follow-up.

Conversion scripts are at `/tmp/convert-disables2.py` (generic) and `/tmp/convert-hooks-disables2.py` (hooks-specific). Both can be re-run after each remediation pass. Multi-rule disables and block-form `/* eslint-disable foo */ ... /* eslint-enable */` were skipped; both would need a more elaborate mapping (Biome has no block-form ignore — block disables would expand to per-line `biome-ignore` on every line that triggers within the block).

### Recommended remediation order

1. **Trivial mechanical** (`useOptionalChain`, `noImplicitAnyLet`, `noShadowRestrictedNames`, `useTemplate`, `useNodejsImportProtocol`, `noBannedTypes`): batch-apply codemods. ~120 fixes, low risk.
2. **Real bugs** (`useIterableCallbackReturn`, `noNonNullAssertedOptionalChain`, `useJsxKeyInIterable`, `noDuplicateProperties`, `noEmptyCharacterClassInRegex`, `noAccumulatingSpread`): each is likely a latent defect. ~85 fixes, needs review.
3. **a11y audit** (`noSvgWithoutTitle`, `noStaticElementInteractions`, `useSemanticElements`, `useAriaProps*`, `useKeyWithClickEvents`, `noLabelWithoutControl`, `useHtmlLang`, `noNoninteractiveTabindex`, `noNoninteractiveElementToInteractiveRole`): ~60 sites. Requires UX judgment per site (meaningful icon vs decorative; button vs div).
4. **Hooks audit** (`useExhaustiveDependencies`, `useHookAtTopLevel`): ~210 sites. Many will be legit `// eslint-disable` carry-overs that need `// biome-ignore` equivalents with a stated reason. Some will be real stale-closure bugs.
5. **Unused / cleanup** (`noUnusedImports`, `noUnusedVariables`, `noUnusedFunctionParameters`): ~290 sites. Can be partially auto-fixed with `biome check --write --unsafe` but needs review since some unused vars/params are signature-driven.

Each block above is a candidate follow-up ticket. They are independent of one another and of the Biome migration itself.

## What's lost vs the prior ESLint stack

Documented losses (Biome has no equivalent, no plugin available, and we declined to substitute):

- **`eslint-plugin-jsdoc` `@swagger` JSDoc enforcement** on `privacy-center/pages/api/*`. The JSDoc blocks and `next-swagger-doc` stay (they feed `pages/api/openapi.json.ts`). Convention-only until the follow-up ticket restores the rendered Swagger UI docs page (`clients/privacy-center/app/docs/page.tsx`, commented out during the React 19 upgrade), at which point missing blocks become visibly broken and self-enforcing.
- **`eslint-plugin-storybook`**. Storybook-specific lint rules removed from fidesui. Storybook itself unaffected.
- **`jsx-a11y` custom component mappings.** The prior ESLint config mapped Ant Design components (`Button`, `Select`, `AutoComplete`, `DatePicker`, etc.) to their native equivalents so a11y rules would fire on them. Biome's a11y rules don't support custom component mappings, so a11y checks on Ant components will be skipped silently. This is a real regression for new code; for existing code, the warnings table above suggests we weren't catching much anyway.
- **`eslint-plugin-tailwindcss` unknown class detection.** Biome's `useSortedClasses` handles sorting but doesn't validate that class names exist in the Tailwind config. Typos in classnames will compile and ship. (Sorting is also gated on the nursery `useSortedClasses` rule, currently not enabled.)
- **`airbnb` stylistic strictness.** Many small stylistic rules (function expression style, naming conventions, max-classes-per-file, etc.) simply go away. Biome's `style` group is leaner. We considered this a feature, not a bug.

## What's retained as-is

- `antd lint` (`@ant-design/cli`) still runs in admin-ui, privacy-center, fidesui. Orthogonal to ESLint/Prettier.
- TypeScript via `tsc --noEmit` still runs per package via turbo.
- Jest unit tests, Cypress E2E, build steps — untouched.

## Editor experience

`.vscode/settings.json` now:

- Default formatter: `biomejs.biome` (was Prettier).
- On save (for JS/JSX/TS/TSX/JSON): `source.fixAll.biome` + `source.organizeImports.biome`.
- Python (ruff) and markdown blocks untouched.

`.vscode/extensions.json` recommends `biomejs.biome`, marks Prettier and ESLint extensions as `unwantedRecommendations`. You'll need to install the Biome extension on your machine.

## Followups to track if we ship

1. Re-enable the privacy-center Swagger UI docs page (`clients/privacy-center/app/docs/page.tsx`, blocked by React 19 + `swagger-ui-react`; likely resolved in v5.30+).
2. One ticket per warning category from the table above, scoped to roughly the listed counts.
3. Cleanup pass to delete dead `// eslint-disable*` comments (461 instances in source). They are inert under Biome but ugly.
4. Re-promote the downgraded rules from `warn` to `error` after each remediation pass completes.

## Decision gate

Three outcomes:

- **Ship.** Merge as-is, work the follow-up tickets in priority order.
- **Ship with deferred follow-ups.** Same as above but block on creating the tickets first.
- **Abandon.** Throw away the branch, open a ticket for ESLint v9 flat-config migration instead.
