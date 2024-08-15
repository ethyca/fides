module.exports = {
  extends: [
    "airbnb",
    "airbnb-typescript/base",
    "plugin:prettier/recommended",
    "next/core-web-vitals",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: "module",
    project: "tsconfig.json",
    tsconfigRootDir: __dirname,
    createDefaultProgram: true,
  },
  root: true,
  rules: {
    // "curly": ["error", "all"],
    // "nonblock-statement-body-position": ["error", "below"],
    // "import/prefer-default-export": "off",
    "react/jsx-filename-extension": [1, { extensions: [".tsx"] }],
    "react/jsx-props-no-spreading": [0],
    "react/function-component-definition": [
      2,
      {
        namedComponents: "arrow-function",
      },
    ],
    "react/require-default-props": "off",
    "prettier/prettier": "warn",
  },
};
