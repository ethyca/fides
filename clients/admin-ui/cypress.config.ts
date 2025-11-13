import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:3000",
    experimentalRunAllSpecs: true,
    setupNodeEvents(on, config) {
      on("before:browser:launch", (browser, launchOptions) => {
        if (browser.family === "chromium") {
          // No need for tests to be slowed down by animations!
          launchOptions.args.push("--force-prefers-reduced-motion");
        }
        return launchOptions;
      });

      // Delete videos for passing tests to save disk space and speed up CI
      // Videos for failures are kept for debugging
      on("after:spec", (spec, results) => {
        if (results && results.video && results.stats.failures === 0) {
          // Delete video if test passed
          const fs = require("fs");
          if (fs.existsSync(results.video)) {
            fs.unlinkSync(results.video);
          }
        }
      });

      return config;
    },
  },

  defaultCommandTimeout: 4000,

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

  // Will only run for cy:run, not cy:open
  video: true,
});
