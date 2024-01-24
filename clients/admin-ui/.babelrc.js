// Enable istanbul for code coverage reporting in Cypress tests (npm run cy:start)
const ADD_CODE_COVERAGE = process.env.NODE_ENV === "test";

module.exports = {
  presets: ["next/babel"],
  plugins: ADD_CODE_COVERAGE ? ["istanbul"] : [],
};
