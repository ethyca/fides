module.exports = {
  extends: ["next/core-web-vitals"],
  parserOptions: {
    project: "tsconfig.json",
    tsconfigRootDir: __dirname,
  },
  parser: "@typescript-eslint/parser",
  overrides: [
    {
      // Require Swagger JSdoc for all /api routes
      files: ["pages/api/**/*.ts"],
      plugins: ["jsdoc"],
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
  ],
  rules: {},
};
