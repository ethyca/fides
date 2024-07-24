module.exports = {
  extends: [
    "airbnb",
    "airbnb-typescript/base",
    "next/core-web-vitals",
    "plugin:prettier/recommended",
  ],
  plugins: ["simple-import-sort"],
  rules: {
    // "curly": ["error", "all"],
    // "nonblock-statement-body-position": ["error", "below"],
    // "import/prefer-default-export": "off",
    "react/jsx-key": ["error", { checkFragmentShorthand: true }],
    "react/jsx-filename-extension": [1, { extensions: [".tsx"] }],
    "react/jsx-props-no-spreading": [0],
    "react/function-component-definition": [
      2,
      {
        namedComponents: "arrow-function",
      },
    ],
    "react/require-default-props": "off",
    "simple-import-sort/imports": "error",
    "simple-import-sort/exports": "error",
    "prettier/prettier": "warn",
    "@typescript-eslint/ban-types": [
      "error",
      {
        types: {
          "React.FC": {
            message:
              "Remove entirely and allow Typescript to infer JSX.Element.",
          },
        },
      },
    ],
  },
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: "module",
    project: "./tsconfig.json",
    tsconfigRootDir: __dirname,
    createDefaultProgram: true,
  },
};
