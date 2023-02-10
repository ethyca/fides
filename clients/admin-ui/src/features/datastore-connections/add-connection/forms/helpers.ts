import { ConnectionTypeSecretSchemaReponse } from "~/features/connection-type/types";

/**
 * Fill in default values based off of a schema
 */
export const fillInDefaults = (
  defaultValues: Record<string, any>,
  connectionSchema: {
    properties: ConnectionTypeSecretSchemaReponse["properties"];
  }
) => {
  const filledInValues = { ...defaultValues };
  Object.entries(connectionSchema.properties).forEach((key) => {
    const [name, schema] = key;

    if (schema.type === "integer") {
      filledInValues[name] = schema.default ? Number(schema.default) : 0;
    } else {
      filledInValues[name] = schema.default ?? "";
    }
  });
  return filledInValues;
};
