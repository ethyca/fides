module.exports = {
  extends: ["next/core-web-vitals", "plugin:tailwindcss/recommended"],
  parserOptions: {
    project: "tsconfig.json",
    tsconfigRootDir: __dirname,
  },
  rules: {
    // since we are using static site export
    "@next/next/no-img-element": "off",
  },
};
