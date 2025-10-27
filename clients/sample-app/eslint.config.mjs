import tseslint from "typescript-eslint";
import react from "eslint-plugin-react";
import prettier from "eslint-plugin-prettier/recommended";

export default tseslint.config(prettier, {
  plugins: {
    react,
  },
  languageOptions: {
    parser: tseslint.parser,
    parserOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      projectService: true,
      tsconfigRootDir: import.meta.dirname,
    },
  },
  rules: {
    "react/jsx-filename-extension": [1, { extensions: [".tsx"] }],
    "react/jsx-props-no-spreading": [0],
    "react/function-component-definition": [
      2,
      {
        namedComponents: "arrow-function",
      },
    ],
    "react/require-default-props": "off",
    "prettier/prettier": "warn",
  },
});
