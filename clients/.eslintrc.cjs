module.exports = {
  extends: ["airbnb", "airbnb-typescript", "plugin:prettier/recommended"],
  plugins: ["simple-import-sort"],
  root: true,
  rules: {
    curly: ["error", "all"],
    "nonblock-statement-body-position": ["error", "below"],
    "react/function-component-definition": [
      2,
      { namedComponents: "arrow-function" },
    ],
    "react/jsx-filename-extension": ["warn", { extensions: [".tsx"] }],
    "react/jsx-key": ["error", { checkFragmentShorthand: true }],
    "react/jsx-props-no-spreading": "off",
    "simple-import-sort/imports": "error",
    "simple-import-sort/exports": "error",
    // Default exports are slightly preferred for component files, but this rule has too many false positives.
    "import/prefer-default-export": "off",
    // since defaultProps are deprecated for function components
    "react/require-default-props": "off",
    // Redux Toolkit reducers pass writable drafts for state updates which are cleaner than object spreading.
    "no-param-reassign": [
      "error",
      {
        props: true,
        ignorePropertyModificationsForRegex: ["^draft"],
      },
    ],
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
    "prettier/prettier": "warn",
  },
};
