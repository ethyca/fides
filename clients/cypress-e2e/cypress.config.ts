import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    // Enabled in order to pass custom commands to origin blocks
    // https://docs.cypress.io/api/commands/origin#Dependencies--Sharing-Code
    experimentalOriginDependencies: true,
  },
});
