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
  transform: {
    // Use babel-jest to transpile tests with the next/babel preset
    // https://jestjs.io/docs/configuration#transform-objectstring-pathtotransformer--pathtotransformer-object
    "^.+\\.(js|jsx|ts|tsx|mjs)$": ["babel-jest", { presets: ["next/babel"] }],
  },
  moduleDirectories: ["node_modules", "../node_modules", "../fides-js/node_modules"],
  moduleNameMapper: {
    // Handle module aliases
    "^~/(.*)$": "<rootDir>/$1",
    // Handle local packages from our npm workspace
    "^fides-js$": "<rootDir>/../fides-js/dist/fides.mjs",
    // Handle imported module from fides-js (TODO: this doesn't work, clearly node module resolution isn't working!)
    "^typescript-cookie$": "<rootDir>/../node_modules/typescript-cookie/index.js",
  },
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)