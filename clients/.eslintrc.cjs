module.exports = {
  extends: ["airbnb", "airbnb-typescript", "plugin:prettier/recommended"],
  plugins: ["simple-import-sort"],
  root: true,
  settings: {
    "jsx-a11y": {
      components: {
        AutoComplete: "input",
        Button: "button",
        Checkbox: "checkbox",
        DatePicker: "input",
        DocsLink: "a",
        EthycaLogo: "svg",
        FloatButton: "button",
        Form: "form",
        Icon: "svg",
        Image: "img",
        Input: "input",
        "Input.Search": "input",
        InputNumber: "input",
        Link: "a",
        NextLink: "a",
        Radio: "radio",
        RouterLink: "a",
        Select: "select",
        Slider: "input",
        Switch: "checkbox",
        TimePicker: "input",
        TreeSelect: "select",
        Typography: "span",
        "Typography.Text": "span",
        Text: "span",
        "Text.Paragraph": "p",
        Paragraph: "p",
        "Typography.Title": "header",
        Title: "header",
      },
    },
  },
  rules: {
    "jsx-a11y/label-has-associated-control": [
      "error",
      { assert: "either", depth: 25 }, // overrides airbnb to be "either" instead of "both" which is too strict for this project. TODO: maybe remove this rule as part of Ant Forms migration
    ],
    "jsx-a11y/no-autofocus": "off",
    "jsx-a11y/anchor-ambiguous-text": "error", // more strict than airbnb
    "jsx-a11y/no-aria-hidden-on-focusable": "error", // more strict than airbnb
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
