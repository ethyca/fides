module.exports = {
  env: {
    browser: true,
    es2021: true,
  },

  parser: "@typescript-eslint/parser",

  parserOptions: {
    project: "tsconfig.json",
    tsconfigRootDir: __dirname,
  },

  rules: {
    "import/no-extraneous-dependencies": "off",
    "react/react-in-jsx-scope": "off",
    "@typescript-eslint/no-throw-literal": "off",
  },

  extends: ["plugin:storybook/recommended"],
};
