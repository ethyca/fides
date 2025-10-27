import js from "@eslint/js";
import tseslint from "typescript-eslint";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import prettier from "eslint-plugin-prettier/recommended";

export default tseslint.config(
  {
    ignores: [
      "node_modules/**",
      "dist/**",
      "jest.config.js",
      "rollup.config.mjs",
      ".eslintrc*",
      "src/lib/gpp/modules/**",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  prettier,
  {
    plugins: {
      react,
      "react-hooks": reactHooks,
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
        pragma: "h",
        version: "18.0",
      },
    },
    rules: {
      // Preact-specific rules
      "import/no-cycle": "off",
      "import/extensions": "off",
      "react/prop-types": "off",
      "no-undef": "off",
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { varsIgnorePattern: "^_" },
      ],
      // Prevent ~/ imports in .ts files
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["~/*"],
              message:
                "The ~/ path alias should not be used in .ts files. Use relative paths instead.",
            },
          ],
        },
      ],
    },
  },
  {
    // Override for test files
    files: ["**/__tests__/**"],
    rules: {
      "no-restricted-imports": "off",
    },
  }
);

