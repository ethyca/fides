/// <reference types="node" />
import { defineConfig } from "cypress";
import { unlinkSync } from "fs";

export default defineConfig({
  viewportWidth: 1200,
  viewportHeight: 800,

  e2e: {
    baseUrl: "http://localhost:3000",
    experimentalRunAllSpecs: true,
    setupNodeEvents(on) {
      on("before:browser:launch", (browser, launchOptions) => {
        if (browser.family === "chromium") {
          // No need for tests to be slowed down by animations!
          launchOptions.args.push("--force-prefers-reduced-motion");
        }
        return launchOptions;
      });

      // Only keep videos for failed tests
      on("after:spec", (spec, results) => {
        if (results && results.video) {
          const failures = results.tests?.some((test) =>
            test.attempts.some((attempt) => attempt.state === "failed"),
          );
          if (!failures) {
            unlinkSync(results.video);
          }
        }
      });
    },
  },

  defaultCommandTimeout: 3000,

  retries: {
    runMode: 2,
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
