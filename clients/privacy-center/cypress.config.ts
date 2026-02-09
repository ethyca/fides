import { defineConfig } from "cypress";
import fs from "fs";

export default defineConfig({
  viewportWidth: 1200,
  viewportHeight: 800,

  e2e: {
    baseUrl: "http://localhost:3001",
    experimentalRunAllSpecs: true,
    // Only keep videos from failures
    // Copied from https://docs.cypress.io/guides/guides/screenshots-and-videos#Delete-videos-for-specs-without-failing-or-retried-tests
    setupNodeEvents(on, config) {
      on(
        "after:spec",
        (spec: Cypress.Spec, results: CypressCommandLine.RunResult) => {
          if (results && results.video) {
            // Do we have failures for any retry attempts?
            const failures = results.tests.some((test) =>
              test.attempts.some((attempt) => attempt.state === "failed"),
            );
            if (!failures) {
              // delete the video if the spec passed, the video exists, and no tests retried
              if (fs.existsSync(results.video)) {
                fs.unlinkSync(results.video);
              }
            }
          }
        },
      );
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

  env: {
    API_URL: "http://localhost:8080/api/v1",
  },
  // Will only run for cy:run, not cy:open
  video: true,
});
