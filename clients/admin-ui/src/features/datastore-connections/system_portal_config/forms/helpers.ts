import { ConnectionTypeSecretSchemaResponse } from "~/features/connection-type/types";
import { ConnectionSystemTypeMap } from "~/types/api/models/ConnectionSystemTypeMap";
import { SystemType } from "~/types/api/models/SystemType";

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

/**
 *
 * Auto-generate an integration key based on the system name
 *
 */
export const generateIntegrationKey = (
  systemFidesKey: string,
  connectionOption: Pick<ConnectionSystemTypeMap, "identifier" | "type">,
): string => {
  let integrationKey = systemFidesKey.replace(/[^A-Za-z0-9\-_]/g, "");

  if (!integrationKey.includes(connectionOption.identifier)) {
    integrationKey += `_${connectionOption.identifier}`;
  }

  if (connectionOption.type === SystemType.SAAS) {
    integrationKey += "_api";
  }

  return integrationKey;
};
