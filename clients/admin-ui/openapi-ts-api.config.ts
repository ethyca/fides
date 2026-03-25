// eslint-disable-next-line import/no-extraneous-dependencies
import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8080/openapi.json",
  output: {
    path: "./src/types/api",
    format: "prettier",
    fileName: {
      suffix: null,
    },
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
        DATAMAP_GROUPING: (schema) => {
          // Replace commas and spaces in enum values to produce valid identifier keys
          if (schema.enum && Array.isArray(schema.enum)) {
            // eslint-disable-next-line no-param-reassign
            schema["x-enum-varnames"] = schema.enum.map((value: string) =>
              value
                .toUpperCase()
                .replace(/,\s*/g, "_")
                .replace(/\s+/g, "_")
                .replace(/-/g, "_"),
            );
          }
        },
        AllowedTypes: (schema) => {
          // Assign distinct enum key names since both values would map to STRING
          if (schema.enum && Array.isArray(schema.enum)) {
            // eslint-disable-next-line no-param-reassign
            schema["x-enum-varnames"] = schema.enum.map((value: string) => {
              if (value === "string") {
                return "STRING";
              }
              if (value === "string[]") {
                return "STRING_ARRAY";
              }
              return value.toUpperCase().replace(/[^A-Z0-9]/g, "_");
            });
          }
        },
        // -- Fidesplus computed properties not in base OpenAPI spec --
        StagedResourceAPIResponse: (schema: any) => {
          schema.properties.preferred_data_uses = {
            type: "array",
            items: { type: "string" },
            nullable: true,
            description:
              "Computed: user_assigned_data_uses ?? data_uses (fidesplus)",
          };
        },
        Field: (schema: any) => {
          schema.properties.preferred_data_categories = {
            type: "array",
            items: { type: "string" },
            nullable: true,
            description: "Computed: field_data_categories (fidesplus)",
          };
          // Remove additionalProperties to prevent catch-all index signature
          // that causes TypeScript to resolve all properties to `{}`
          delete schema.additionalProperties;
        },
        ExperienceConfigCreate: (schema: any) => {
          schema.properties.resurface_behavior = {
            type: "array",
            items: { type: "string", enum: ["reject", "dismiss"] },
            nullable: true,
            description: "Resurface behavior options (fidesplus)",
          };
        },
        ExperienceConfigUpdate: (schema: any) => {
          schema.properties.resurface_behavior = {
            type: "array",
            items: { type: "string", enum: ["reject", "dismiss"] },
            nullable: true,
            description: "Resurface behavior options (fidesplus)",
          };
        },
        SystemStagedResourcesAggregateRecord: (schema: any) => {
          schema.properties.metadata = {
            $ref: "#/components/schemas/IdentityProviderApplicationMetadata",
            nullable: true,
            description:
              "Okta application metadata for identity provider resources (fidesplus)",
          };
        },
      },
    },
    hooks: {
      symbols: {
        getFilePath: (symbol) => {
          // Skip endpoint-specific types (camelCase pattern: operationNameApiV1PathMethodData/Response/Errors/etc)
          // These are auto-generated for each endpoint and bloat the output
          if (
            symbol.name &&
            /Api[A-Z].*(?:Data|Response|Responses|Error|Errors)$/.test(
              symbol.name,
            )
          ) {
            // Return undefined to skip this symbol entirely
            return undefined;
          }

          // Keep one type/enum per file in models/ directory
          // Note: enums have kind: undefined, only types have kind: "type"
          // So we match on any symbol with a name (enums, types, interfaces all get split)
          if (symbol.name) {
            return `models/${symbol.name}`;
          }
          // Let other symbols use default placement
          return undefined;
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
