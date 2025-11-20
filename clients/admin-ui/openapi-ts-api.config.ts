// eslint-disable-next-line import/no-extraneous-dependencies
import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8080/openapi.json",
  output: {
    path: "./src/types/api",
    format: "prettier",
  },
  plugins: ["@hey-api/typescript"],
});
