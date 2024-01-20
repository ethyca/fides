/* eslint-disable import/no-extraneous-dependencies */
import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:3000",
    setupNodeEvents(on, config) {
      require("@cypress/code-coverage/task")(on, config)
      return config
    },
  },

  defaultCommandTimeout: 5000,

  retries: {
    runMode: 3,
    openMode: 0,
  },

  component: {
    devServer: {
      framework: "next",
      bundler: "webpack",
    },
  },
});
