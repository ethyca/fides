// jest.config.js
module.exports = {
  collectCoverageFrom: [
    "**/*.{js,jsx,ts,tsx}",
    "!**/*.d.ts",
    "!**/node_modules/**",
  ],
  moduleNameMapper: {
    // Handle CSS imports (with CSS modules)
    // https://jestjs.io/docs/webpack#mocking-css-modules
    "^.+\\.module\\.(css|sass|scss)$": "identity-obj-proxy",

    // Handle CSS imports (without CSS modules)
    "^.+\\.(css|sass|scss)$": "<rootDir>/__mocks__/styleMock.js",

    // Handle image imports
    // https://jestjs.io/docs/webpack#handling-static-assets
    "^.+\\.(png|jpg|jpeg|gif|webp|avif|ico|bmp|svg)$/i": `<rootDir>/__mocks__/fileMock.js`,

    // Handle module aliases
    "^@/components/(.*)$": "<rootDir>/components/$1",
    "^app/(.*)$": "<rootDir>/src/app/$1",
    "^common/(.*)$": "<rootDir>/src/features/common/$1",
    "^connection-type/(.*)$": "<rootDir>/src/features/connection-type/$1",
    "^datastore-connections/(.*)$":
      "<rootDir>/src/features/datastore-connections/$1",
    "^privacy-requests/(.*)$": "<rootDir>/src/features/privacy-requests/$1",
    "^subject-request/(.*)$": "<rootDir>/src/features/subject-request/$1",
    "^user-management/(.*)$": "<rootDir>/src/features/user-management/$1",
  },
  // Add more setup options before each test is run
  setupFilesAfterEnv: ["<rootDir>/__tests__/jest.setup.ts"],
  testPathIgnorePatterns: [
    "<rootDir>/node_modules/",
    "<rootDir>/.next/",
    "jest.setup.ts",
    "test-utils.tsx",
  ],
  testEnvironment: "jsdom",
  transform: {
    // Use babel-jest to transpile tests with the next/babel preset
    // https://jestjs.io/docs/configuration#transform-objectstring-pathtotransformer--pathtotransformer-object
    "^.+\\.(js|jsx|ts|tsx)$": ["babel-jest", { presets: ["next/babel"] }],
  },
  transformIgnorePatterns: [
    "/node_modules/",
    "^.+\\.module\\.(css|sass|scss)$",
  ],
};
