const { pathsToModuleNameMapper } = require("ts-jest");
const { compilerOptions } = require("./tsconfig");

/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  coverageReporters: ["json-summary"],
  preset: "ts-jest",
  testEnvironment: "jsdom",
  setupFiles: ["./__tests__/setup.ts"],
  modulePaths: [compilerOptions.baseUrl],
  moduleNameMapper: {
    ...pathsToModuleNameMapper(compilerOptions.paths),
  },
  testPathIgnorePatterns: ["/dist/", "__utils__", "__tests__/setup\\.ts"],
  watchPathIgnorePatterns: ["/dist/"],
};
