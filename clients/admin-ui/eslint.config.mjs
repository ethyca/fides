import baseConfig from "../eslint.config.mjs";
import tailwindcss from "eslint-plugin-tailwindcss";
import importPlugin from "eslint-plugin-import";
import tseslint from "typescript-eslint";

export default tseslint.config(
  // Extend base config (includes all React, React Hooks, JSX A11y, Tier 1 rules, etc.)
  ...baseConfig,

  // Admin-UI specific ignores
  {
    ignores: ["cypress/**", "postcss.config.js", "tailwind.config.js"],
  },

  // Admin-UI specific configuration
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
            "eslint.config.mjs", // ESLint config can import dev dependencies
          ],
        },
      ],
      "tailwindcss/classnames-order": "warn",
      "tailwindcss/no-custom-classname": "warn",
    },
  },
);
