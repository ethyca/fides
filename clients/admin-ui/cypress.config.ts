import { defineConfig } from "cypress";

export default defineConfig({
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
