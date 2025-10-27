import tseslint from "typescript-eslint";
import cypress from "eslint-plugin-cypress/flat";
import noOnlyTests from "eslint-plugin-no-only-tests";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import prettier from "eslint-plugin-prettier/recommended";

export default tseslint.config(cypress.configs.recommended, prettier, {
  plugins: {
    "no-only-tests": noOnlyTests,
    "simple-import-sort": simpleImportSort,
  },
  languageOptions: {
    parser: tseslint.parser,
    parserOptions: {
      projectService: true,
      tsconfigRootDir: import.meta.dirname,
    },
  },
  rules: {
    "no-console": "warn",
    "no-only-tests/no-only-tests": "error",
    "cypress/unsafe-to-chain-command": "off",
    "simple-import-sort/imports": "error",
    "simple-import-sort/exports": "error",
    "prettier/prettier": "warn",
  },
});

