import js from "@eslint/js";
import { fixupPluginRules } from "@eslint/compat";
import tseslint from "typescript-eslint";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import jsxA11y from "eslint-plugin-jsx-a11y";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import prettier from "eslint-plugin-prettier/recommended";

export default tseslint.config(
  {
    ignores: ["**/.eslintrc*"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  jsxA11y.flatConfigs.recommended,
  prettier,
  {
    plugins: {
      react,
      "react-hooks": fixupPluginRules(reactHooks),
      "simple-import-sort": simpleImportSort,
    },
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    settings: {
      react: {
        version: "detect",
      },
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
        { assert: "either", depth: 25 },
      ],
      "jsx-a11y/no-autofocus": "off",
      "jsx-a11y/anchor-ambiguous-text": "error",
      "jsx-a11y/no-aria-hidden-on-focusable": "error",
      curly: ["error", "all"],
      "nonblock-statement-body-position": ["error", "below"],
      "react/function-component-definition": [
        2,
        { namedComponents: "arrow-function" },
      ],
      "react/jsx-filename-extension": ["warn", { extensions: [".tsx"] }],
      "react/jsx-key": ["error", { checkFragmentShorthand: true }],
      "react/jsx-props-no-spreading": "off",
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
      "import/prefer-default-export": "off",
      "react/require-default-props": "off",
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
  }
);

