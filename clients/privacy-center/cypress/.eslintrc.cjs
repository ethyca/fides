module.exports = {
  extends: ["plugin:cypress/recommended", "plugin:prettier/recommended"],
  plugins: [
    "no-only-tests",
    "cypress",
    "simple-import-sort",
    "@typescript-eslint",
    "import",
  ],
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: {
    project: "./tsconfig.json",
    tsconfigRootDir: __dirname,
  },
  rules: {
    "no-console": "warn",
    "no-only-tests/no-only-tests": "error",
    "cypress/unsafe-to-chain-command": "off",
    "simple-import-sort/imports": "error",
    "simple-import-sort/exports": "error",
    "prettier/prettier": "warn",
  },
};
