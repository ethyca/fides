/* eslint-disable import/no-extraneous-dependencies */
import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:3000",
  },
  defaultCommandTimeout: 5000,
  retries: {
    runMode: 3,
    openMode: 0,
  },
});
