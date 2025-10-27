import jsdoc from "eslint-plugin-jsdoc";
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
      ".eslintrc*",
    ],
  },
  {
    plugins: {
      jsdoc,
      "@typescript-eslint": tseslint.plugin,
    },
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {},
  },
  {
    // Require Swagger JSdoc for all /api routes
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
