# ESLint v9 PoC — ENG-3785

Parallel PoC to the Biome branch. Upgrades the `clients/` monorepo from ESLint 8 (with airbnb / airbnb-typescript / preact / tailwindcss-plugin) to ESLint 9.39 with a flat config, modern plugin versions, and the airbnb stack abandoned.

The goal is the same as the Biome PoC: stop fighting outdated tooling, decide whether to keep ESLint (modernized) or replace it with Biome.

## TL;DR

- **CI is green locally.** `npm run check:ci` exits 0. No errors. 545 warnings (latent issues newer rule versions surface).
- **Config file count:** 19 → 2. Single `eslint.config.mjs` + single `.prettierignore` at `clients/` root replace 9 `.eslintrc.cjs` + 4 `.prettierignore` + 4 `.eslintignore` files. (Biome PoC: 19 → 1.)
- **Lint runtime:** ~30 seconds for 2,750 files (ESLint v9 with --fix off). Roughly 60x slower than Biome's 0.5s; about the same as ESLint v8 was.
- **No rule porting.** Stock `recommended` from each plugin. The only rule edits are off/warn toggles, matching the Biome PoC's approach.
- **Decision asked:** keep modernized ESLint, switch to Biome, or stay on v8 (do nothing).

## What changed

| Before | After |
|---|---|
| ESLint 8.57 | ESLint 9.39.4 (flat config) |
| 9 `.eslintrc.cjs` (root + 5 packages + 3 cypress/test subdirs) | 1 `eslint.config.mjs` at `clients/` root |
| 4 `.prettierignore` (one per package) | 1 `.prettierignore` at `clients/` root |
| `@typescript-eslint/eslint-plugin` + `@typescript-eslint/parser` 7.17/8.57 mix | `typescript-eslint` 8.59 (combined package) |
| `eslint-plugin-react-hooks` 4.6.2 | `eslint-plugin-react-hooks` 7.1 (significantly stricter; React Compiler-aware) |
| `eslint-plugin-import` 2.x | `eslint-plugin-import-x` 4.x (better TS perf; v9 compat) |
| `eslint-config-next` 14/15 | `@next/eslint-plugin-next` 16 (flat config) |
| `eslint-plugin-cypress` 3.4 | `eslint-plugin-cypress` 6.4 (flat config, new rules) |
| `eslint-plugin-jsx-a11y` 6.9, `eslint-plugin-jsdoc` 48, `eslint-plugin-storybook` 0.x | 6.10, 62, 10 (all flat-config-native) |
| `eslint-config-airbnb` + `eslint-config-airbnb-typescript` | *removed* |
| `eslint-config-preact` (fides-js) | *removed* |
| `eslint-plugin-tailwindcss` (admin-ui) | *removed* (Tailwind classname linting not replaced) |
| `eslint-plugin-prettier` + `eslint-config-prettier` | *removed* (Prettier runs separately) |
| Prettier 3.8.3 | Prettier 3.8.3 (unchanged) |
| `lint-staged`: `prettier --write` + `eslint --fix` | same (unchanged) |
| VS Code config | unchanged (still wires `source.fixAll.eslint` on save) |

## Configuration

`clients/eslint.config.mjs`:

- `eslintJs.configs.recommended` + `tseslint.configs.recommended` baseline.
- Plugin recommended configs spread per file scope:
  - All JS/TS/TSX: react, react-hooks, jsx-a11y, simple-import-sort (recommended sets).
  - admin-ui + privacy-center + sample-app: `@next/next` (recommended + core-web-vitals).
  - privacy-center API routes: jsdoc `require-jsdoc` (configured to require `@swagger`-style blocks on exported handlers).
  - fides-js: `no-restricted-imports` for `~/*` aliases (Preact convention from the prior config).
  - fidesui stories: storybook recommended.
  - Cypress dirs: cypress recommended + no-only-tests.
  - Test files: relax unused-vars.
- Two project-wide opt-outs match prior policy: `@typescript-eslint/no-explicit-any` off, `@typescript-eslint/no-unused-vars` set to warn with `_` prefix exemption.
- ~20 rules downgraded from error to warn to keep CI green (see "Warnings outstanding" below). Same pattern as the Biome PoC.

## Diff scope

- **Setup commit (1):** 30 files. Add `eslint.config.mjs`, `.prettierignore`, update root + per-package `package.json`, update `turbo.json`, delete the 19 old config files, regenerate lockfiles. ~2,700 insertions / ~8,800 deletions (almost all package-lock churn from removing airbnb's transitive deps).
- **Autofix commit (2):** 710 files, +168 / -904. Almost entirely automatic removal of inline `// eslint-disable-next-line <rule>` comments targeting rules no longer in the new config (airbnb-specific, preact-specific, tailwindcss-plugin, and rules whose namespace changed in typescript-eslint v8). ESLint v9's `reportUnusedDisableDirectives` is on by default; `--fix` strips them. **No React hook dependency arrays modified.**

## Warnings outstanding (545 total)

Same approach as the Biome PoC: rules that surface lots of net-new findings are downgraded from error to warn so CI stays green; each is a follow-up remediation.

| Rule | Count | New in this stack? |
|---|---:|---|
| `react-hooks/set-state-in-effect` | **121** | Yes (react-hooks v7; flags `setState` inside `useEffect` unconditionally) |
| `cypress/unsafe-to-chain-command` | **97** | Yes (cypress-plugin v6) |
| `@typescript-eslint/no-unused-vars` | 83 | Same as before |
| `@typescript-eslint/no-require-imports` | 43 | Yes (recommended in v8) |
| `@typescript-eslint/no-unused-expressions` | 39 | Yes (recommended in v8) |
| `no-restricted-imports` | 26 | Same — fides-js `~/*` imports (was already a rule) |
| `jsx-a11y/no-autofocus` | 24 | Yes (recommended in 6.10) |
| `@typescript-eslint/no-empty-object-type` | 23 | Yes (replaces airbnb's `ban-types`) |
| `react-hooks/preserve-manual-memoization` | 16 | Yes (react-hooks v7 compiler-aware) |
| `react-hooks/refs` | 12 | Yes (react-hooks v7) |
| `react-hooks/immutability` | 10 | Yes (react-hooks v7) |
| `@typescript-eslint/no-non-null-asserted-optional-chain` | 10 | Same as before |
| `react-hooks/incompatible-library` | 9 | Yes (react-hooks v7) |
| `@typescript-eslint/no-namespace` | 6 | Same as before |
| `react-hooks/exhaustive-deps` | 6 | Same rule, stricter analysis |
| Other (~22 single-digit) | 50 | Mix |

**Net-new rule findings: ~395 of 545 (72%).** Most are from upgrading react-hooks 4 → 7, typescript-eslint 7 → 8 recommended, jsx-a11y 6.9 → 6.10, cypress-plugin 3 → 6. The same "stricter-newer-versions" dynamic the Biome PoC documented (Biome's hooks rule is stricter than eslint-plugin-react-hooks v4; react-hooks v7 closes most of that gap but not all).

**Lost coverage vs the old config:**

- **airbnb stylistic rules** — many small rules go away (function expression style, naming conventions, max-classes-per-file, etc.). Considered a feature.
- **`eslint-plugin-tailwindcss`** — class sorting and unknown classname detection gone. No equivalent in Biome either.
- **`@typescript-eslint/ban-ts-comment` with 10-char min description** — typescript-eslint v8 has the rule but no min-length variant.

### Comparison to the Biome PoC

| Metric | Biome PoC | ESLint v9 PoC |
|---|---|---|
| Config files | 1 | 2 (eslint.config.mjs + .prettierignore) |
| Lint runtime (full repo) | ~0.5s | ~30s |
| Warnings remaining | 688 | 545 |
| `useExhaustiveDependencies` / `react-hooks/exhaustive-deps` | 120 (95 extra-dep, 23 missing-dep, 2 instability) | 6 (just missing-dep) |
| `react-hooks/set-state-in-effect`-class | (rolled into 120 above) | 121 (separate rule) |
| net-new findings | ~80% | ~72% |
| Devs need new VS Code extension | Yes (`biomejs.biome`) | No (existing `dbaeumer.vscode-eslint`) |
| Format diff at adoption | ~60 files (Prettier and Biome formatters are close) | 0 (Prettier unchanged) |
| Plugin ecosystem | Native rules only; some gaps (Storybook, jsdoc, tailwind unknown classnames, Ant Design a11y mappings) | Full plugin ecosystem retained |
| Code-style autofix scope | Larger (organizeImports, type-only annotations, etc.) | Smaller (mostly unused-disable cleanup) |
| TypeScript dep-array tracking | Property-level (`tableInstance.getState`) | Object-level (`tableInstance`) |
| "Reports extra/unused deps" | Yes (95 hits) | No |

Both passes converge on a similar end state: green CI, a few hundred warnings to triage, a smaller config surface area. The trade-off is mostly **speed vs. plugin ecosystem**:

- **Biome wins on speed and config simplicity.** One tool, one config, sub-second runs.
- **ESLint v9 wins on ecosystem.** Storybook, jsdoc-with-`@swagger`-style enforcement, Tailwind sorting (different plugin), custom a11y component maps (jsx-a11y supports them), and any future rule someone publishes for a specific framework.

## What's retained

- `antd lint` (`@ant-design/cli`) still runs per package via turbo. Orthogonal.
- TypeScript via `tsc --noEmit` per package.
- Prettier 3.8.3 with one `.prettierignore` at root.
- lint-staged in admin-ui and privacy-center: `prettier --write` + `eslint --fix` (same as before).
- VS Code config: unchanged (existing `dbaeumer.vscode-eslint` works with flat config natively).

## Followups to track if we ship this path

1. Re-enable the privacy-center Swagger UI docs page (same follow-up as the Biome PoC, blocked by React 19 + `swagger-ui-react`).
2. One ticket per warning category from the table above.
3. Cleanup pass to delete dead `// eslint-disable*` comments that no longer reference a known rule (the autofix already removed most; a few block-form ones may remain).
4. Re-promote downgraded rules from `warn` back to `error` after each remediation pass.
5. Consider adopting `eslint-plugin-react-compiler` (officially blessed by the React team) once it's stable, to formalize the React Compiler ruleset that `react-hooks` v7 now ships.

## Decision gate

The two PoC branches are now directly comparable. Three outcomes:

- **Ship Biome** (`gill/ENG-3785/biome-poc`). Maximum speed and config simplicity; accept some plugin coverage loss.
- **Ship ESLint v9** (this branch). Preserve plugin ecosystem and editor familiarity; accept slower runs and a larger config file.
- **Do neither.** Stay on ESLint 8. Note: that increasingly means stale tooling — airbnb 19 has not been updated in 2 years and won't get v9 support.
