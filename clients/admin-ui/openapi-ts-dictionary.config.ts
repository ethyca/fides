// eslint-disable-next-line import/no-extraneous-dependencies
import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8081/openapi.json",
  output: {
    path: "./src/types/dictionary-api",
    format: "prettier",
  },
  types: {
    enums: "typescript",
    identifierCase: "preserve",
  },
});
