module.exports = {
  extends: ["next/core-web-vitals"],
  parserOptions: {
    project: "tsconfig.json",
    tsconfigRootDir: __dirname,
  },
  rules: {
    // since we are using static site export
    "@next/next/no-img-element": "off",
  },
};
