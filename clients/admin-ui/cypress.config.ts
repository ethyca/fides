import { defineConfig } from "cypress";
import * as fs from "fs";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:3000",
    experimentalRunAllSpecs: true,
    setupNodeEvents(on, config) {
      on("before:browser:launch", (browser, launchOptions) => {
        if (browser.family === "chromium" && browser.name !== "electron") {
          // No need for tests to be slowed down by animations!
          launchOptions.args.push("--force-prefers-reduced-motion");
        }
        return launchOptions;
      });

      // Delete videos for passing tests
      on("after:spec", (spec, results) => {
        // If the spec has no failures, delete the video
        if (results && results.video && !results.tests.some(test => test.state === "failed")) {
          // Delete the video if there are no failures
          try {
            fs.unlinkSync(results.video);
          } catch (error) {
            console.warn(`Warning: Could not delete video for passing test: ${error.message}`);
          }
        }
      });
    },
  },

  defaultCommandTimeout: 5000,

  retries: {
    runMode: 3,
    openMode: 0,
  },

  video: true,

  component: {
    devServer: {
      framework: "next",
      bundler: "webpack",
    },
  },
});
