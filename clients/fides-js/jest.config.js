const { pathsToModuleNameMapper } = require("ts-jest");
const { compilerOptions } = require("./tsconfig");

/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  modulePaths: [compilerOptions.baseUrl],
  moduleNameMapper: {
    ...pathsToModuleNameMapper(compilerOptions.paths),

    // NOTE: Jest gets confused by typescript-cookie import for some reason;
    // it's somewhere deep in the bowels of node resolution logic, I assume.
    // There's an issue discussion here with tales of woe, and this helpful
    // comment suggests just taking the loss and swapping in js-cookie when
    // testing instead:
    // https://github.com/carhartl/typescript-cookie/issues/110#issuecomment-1375408191
    ...{
      "typescript-cookie": "js-cookie",
    }
  },
};