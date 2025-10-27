import tailwindcss from "eslint-plugin-tailwindcss";
import importPlugin from "eslint-plugin-import";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      "node_modules/**",
      "dist/**",
      "out/**",
      "public/**/*.js",
      "next.config.js",
      "jest.config.js",
      "cypress.config.ts",
      "cypress/screenshots/**",
      ".eslintrc*",
      "postcss.config.js",
      "tailwind.config.js",
    ],
  },
  {
    plugins: {
      tailwindcss,
      import: importPlugin,
    },
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "import/no-extraneous-dependencies": [
        "error",
        {
          devDependencies: [
            "src/mocks/**",
            "**/*.test.ts",
            "**/*.test.tsx",
            "**/*.spec.ts",
            "**/*.spec.tsx",
            "cypress/**",
          ],
        },
      ],
      "tailwindcss/classnames-order": "warn",
      "tailwindcss/no-custom-classname": "warn",
    },
  },
);
