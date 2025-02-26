module.exports = {
  extends: ["plugin:cypress/recommended"],
  plugins: ["no-only-tests", "cypress"],
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: {
    project: "./tsconfig.json",
    tsconfigRootDir: __dirname,
  },
  rules: {
    "no-only-tests/no-only-tests": "error",
    "cypress/unsafe-to-chain-command": "off",
  },
};
