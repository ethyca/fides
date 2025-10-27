import tseslint from "typescript-eslint";
import cypress from "eslint-plugin-cypress/flat";
import noOnlyTests from "eslint-plugin-no-only-tests";

export default tseslint.config(
  {
    ignores: [".eslintrc.*"],
  },
  cypress.configs.recommended,
  {
  plugins: {
    "no-only-tests": noOnlyTests,
  },
  languageOptions: {
    parser: tseslint.parser,
    parserOptions: {
      projectService: true,
      tsconfigRootDir: import.meta.dirname,
    },
  },
  rules: {
    "no-only-tests/no-only-tests": "error",
    "cypress/unsafe-to-chain-command": "off",
  },
});

