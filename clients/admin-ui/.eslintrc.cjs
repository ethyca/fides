module.exports = {
  extends: ["next/core-web-vitals", "plugin:tailwindcss/recommended"],
  parserOptions: {
    project: "tsconfig.json",
    tsconfigRootDir: __dirname,
  },
  parser: "@typescript-eslint/parser",
  rules: {
    // since we are using static site export
    "@next/next/no-img-element": "off",
    "import/no-extraneous-dependencies": [
      "error",
      {
        devDependencies: [
          "src/mocks/**",
          "**/*.test.ts",
          "**/*.spec.ts",
          "cypress/**",
        ],
      },
    ],
  },
};
