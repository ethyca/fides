// jest.config.js
const nextJest = require("next/jest")

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: "./",
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/__tests__/jest.setup.ts"],
  testEnvironment: "jest-environment-jsdom",
  testPathIgnorePatterns: [ "jest.setup.ts" ],
  moduleDirectories: ["node_modules"],
  moduleNameMapper: {
    // Handle module aliases
    "^~/(.*)$": "<rootDir>/$1",

    // Handle local packages from our npm workspace
    // NOTE: this is pretty messy, but it's because jest doesn't understand how
    // npm workspaces work, so it can't find node_modules installed in the
    // clients/ root directory...
    // See https://github.com/jestjs/jest/issues/5325
    "^fides-js$": "<rootDir>/../fides-js/dist/fides.mjs",
  },
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)