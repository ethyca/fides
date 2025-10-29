import baseConfig from "../eslint.config.mjs";
import jsdoc from "eslint-plugin-jsdoc";
import tseslint from "typescript-eslint";

export default tseslint.config(
  // Extend base config (includes all React, React Hooks, JSX A11y, Tier 1 rules, etc.)
  ...baseConfig,

  // Privacy-Center specific ignores
  {
    ignores: ["cypress/**"],
  },

  // Privacy-Center specific configuration
  {
    plugins: {
      jsdoc,
      "@typescript-eslint": tseslint.plugin,
    },
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        projectService: {
          allowDefaultProject: ["eslint.config.mjs"],
        },
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {},
  },

  // Require Swagger JSdoc for all /api routes
  {
    files: ["pages/api/**/*.ts"],
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "jsdoc/no-missing-syntax": [
        "error",
        {
          contexts: [
            {
              comment: "JsdocBlock:has(JsdocTag[tag=swagger])",
              context: "any",
              message:
                "@swagger documentation is required. See: https://github.com/jellydn/next-swagger-doc",
            },
          ],
        },
      ],
    },
  },
);
