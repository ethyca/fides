import { ConnectionTypeSecretSchemaResponse } from "~/features/connection-type/types";

/**
 * Fill in default values based off of a schema
 */
export const fillInDefaults = (
  defaultValues: Record<string, any>,
  connectionSchema?: {
    properties: ConnectionTypeSecretSchemaResponse["properties"];
  },
) => {
  const filledInValues = { ...defaultValues };
  if (connectionSchema) {
    Object.entries(connectionSchema.properties).forEach((key) => {
      const [name, schema] = key;

      if (!("secrets" in filledInValues)) {
        filledInValues.secrets = {};
      }

      if (schema.type === "integer") {
        filledInValues.secrets[name] = schema.default
          ? Number(schema.default)
          : 0;
      } else {
        filledInValues.secrets[name] = schema.default ?? "";
      }
    });
  }
  return filledInValues;
};
