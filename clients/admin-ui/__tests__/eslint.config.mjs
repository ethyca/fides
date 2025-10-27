import tseslint from "typescript-eslint";

export default tseslint.config({
  rules: {
    "import/no-extraneous-dependencies": "off",
  },
});

