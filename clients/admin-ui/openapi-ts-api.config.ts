// eslint-disable-next-line import/no-extraneous-dependencies
import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8080/openapi.json",
  output: {
    path: "./src/types/api",
    format: "prettier",
  },
  parser: {
    patch: {
      schemas: {
        ScopeRegistryEnum: (schema) => {
          // Add x-enum-varnames to replace colons with underscores in enum keys
          if (schema.enum && Array.isArray(schema.enum)) {
            // eslint-disable-next-line no-param-reassign
            schema["x-enum-varnames"] = schema.enum.map((value: string) =>
              value.toUpperCase().replace(/:/g, "_").replace(/-/g, "_"),
            );
          }
        },
      },
    },
  },
  plugins: [
    {
      name: "@hey-api/typescript",
      enums: "typescript",
      case: "preserve",
    },
  ],
});
