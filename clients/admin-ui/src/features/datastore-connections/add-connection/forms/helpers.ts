import { ConnectionTypeSecretSchemaReponse } from "~/features/connection-type/types";
import { BaseConnectorParametersFields } from "~/features/datastore-connections/add-connection/types";

export const fillInDefaults = (
  defaultValues: BaseConnectorParametersFields,
  connectionSchema: ConnectionTypeSecretSchemaReponse
): BaseConnectorParametersFields => {
  const filledInValues = { ...defaultValues };
  Object.entries(connectionSchema.properties).forEach((key) => {
    const [name, schema] = key;

    if (schema.default) {
      filledInValues[name] = schema.default;
    } else if (schema.type === "integer") {
      filledInValues[name] = 0;
    } else {
      filledInValues[name] = "";
    }
  });
  return filledInValues;
};
