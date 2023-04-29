import { defineConfig } from "cypress";

export default defineConfig({
  projectId: "bauzeh",
  e2e: {
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    // Enabled in order to pass custom commands to origin blocks
    // https://docs.cypress.io/api/commands/origin#Dependencies--Sharing-Code
    experimentalOriginDependencies: true,
  },

  retries: {
    runMode: 3,
    openMode: 0,
  },

  env: {
    // These can be overwritten by exporting `CYPRESS_{name}`, for example
    // export CYPRESS_ADMIN_UI_URL="http://staging.example.com"
    API_URL: "http://localhost:8080/api/v1",
    ADMIN_UI_URL: "http://localhost:8080",
    PRIVACY_CENTER_URL: "http://localhost:3001",
    SAMPLE_APP_URL: "http://localhost:3000",

    // Credentials
    USERNAME: "root_user",
    PASSWORD: "Testpassword1!",
  },
});
