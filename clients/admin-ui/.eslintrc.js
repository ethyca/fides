module.exports = {
  extends: [
    'airbnb',
    'airbnb-typescript/base',
    'prettier',
    'next/core-web-vitals',
  ],
  plugins: ['simple-import-sort'],
  root: true,
  parserOptions: {
    project: './tsconfig.json',
    tsconfigRootDir: __dirname,
  },
  rules: {
    // causes bug in re-exporting default exports, see
    // https://github.com/eslint/eslint/issues/15617
    'no-restricted-exports': [0],
    'import/prefer-default-export': 'off',
    'react/function-component-definition': [
      2,
      {
        namedComponents: 'arrow-function',
      },
    ],
    'react/jsx-filename-extension': [1, { extensions: ['.tsx'] }],
    'react/jsx-props-no-spreading': [0],
    'simple-import-sort/imports': 'error',
    'simple-import-sort/exports': 'error',
  },
};
