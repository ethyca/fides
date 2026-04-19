module.exports = {
  extends: ["next/core-web-vitals", "plugin:tailwindcss/recommended"],
  parserOptions: {
    project: "tsconfig.json",
    tsconfigRootDir: __dirname,
    warnOnUnsupportedTypeScriptVersion: false,
  },
  parser: "@typescript-eslint/parser",
  rules: {
    // since we are using static site export
    "@next/next/no-img-element": "off",
    "tailwindcss/no-custom-classname": [
      "warn",
      { whitelist: ["nodrag", "nopan", "nowheel"] },
    ],
    eqeqeq: ["error", "always"],
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
  },
};
