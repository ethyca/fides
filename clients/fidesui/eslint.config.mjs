import js from "@eslint/js";
import tseslint from "typescript-eslint";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import importPlugin from "eslint-plugin-import";
import storybook from "eslint-plugin-storybook";
import prettier from "eslint-plugin-prettier/recommended";
import globals from "globals";

export default tseslint.config(
  {
    ignores: ["dist/**", ".eslintrc*"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  ...storybook.configs["flat/recommended"],
  prettier,
  {
    plugins: {
      react,
      "react-hooks": reactHooks,
      "simple-import-sort": simpleImportSort,
      import: importPlugin,
    },
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
      parserOptions: {
        projectService: {
          allowDefaultProject: [
            "eslint.config.js",
            ".storybook/*.ts",
            ".storybook/*.tsx",
          ],
        },
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
    },
    rules: {
      "import/no-extraneous-dependencies": "off",
      "react/react-in-jsx-scope": "off",
    },
  },
);
