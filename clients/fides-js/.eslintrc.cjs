module.exports = {
  extends: ["preact"],
  parserOptions: {
    project: "tsconfig.json",
    tsconfigRootDir: __dirname,
  },
  parser: "@typescript-eslint/parser",
  overrides: [
    {
      // Prevent ~/ imports in .ts files
      files: ["**/*.ts"],
      excludedFiles: ["**/__tests__/**"],
      rules: {
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
  ],
  rules: {
    "import/no-cycle": "off",
    "import/extensions": "off",
    "react/prop-types": "off",
    "no-undef": "off",
    "no-unused-vars": "off", // the @typescript-eslint line below is smarter about handling unused variables, taking in to account TS interfaces
    "@typescript-eslint/no-unused-vars": ["error", { varsIgnorePattern: "^_" }],
  },
};
