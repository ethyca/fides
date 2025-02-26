import { ConnectionTypeSecretSchemaResponse } from "~/features/connection-type/types";

/**
 * Fill in default values based off of a schema. Use schema defaults if they exist, otherwise use passed-in defaults
 */
export const fillInDefaults = (
  defaultValues: Record<string, any>,
  connectionSchema: {
    properties: ConnectionTypeSecretSchemaResponse["properties"];
  },
) => {
  const filledInValues = { ...defaultValues };
  Object.entries(connectionSchema.properties).forEach((key) => {
    const [name, schema] = key;

    if (schema.type === "integer") {
      const defaultValue = schema.default
        ? Number(schema.default)
        : defaultValues[name];
      filledInValues[name] = defaultValue || 0;
    } else {
      const defaultValue = schema.default ?? defaultValues[name];
      filledInValues[name] = defaultValue ?? null;
    }
  });
  return filledInValues;
};
