import type { CodegenConfig } from "@graphql-codegen/cli";

/**
 * GraphQL code generation for the dashboard PoC.
 *
 * Reads the local SDL (emitted from fidesplus via `nox -s graphql_emit_schema`)
 * and generates a typed client into src/__generated__/graphql/.
 *
 * Rerun whenever schema.graphql or a *.graphql document changes:
 *   npm run graphql:generate
 */
const config: CodegenConfig = {
  schema: "schema.graphql",
  documents: ["src/**/*.graphql"],
  generates: {
    "src/__generated__/graphql/": {
      preset: "client",
      presetConfig: {
        gqlTagName: "gql",
      },
      config: {
        useTypeImports: true,
        scalars: {
          DateTime: "string",
          JSON: "Record<string, unknown>",
        },
      },
    },
  },
};

export default config;
