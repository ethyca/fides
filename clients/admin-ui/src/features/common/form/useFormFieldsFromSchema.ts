import { cloneDeep } from "lodash";

import {
  ConnectionTypeSecretSchemaProperty,
  ConnectionTypeSecretSchemaResponse,
} from "~/features/connection-type/types";

export const FIDES_DATASET_REFERENCE = "#/definitions/FidesDatasetReference";

export const useFormFieldsFromSchema = (
  secretsSchema?: ConnectionTypeSecretSchemaResponse,
) => {
  const validateField = (
    label: string,
    value: string | undefined,
    type?: string,
  ) => {
    // Required validation is handled by the Form.Item `required` rule in
    // FormFieldFromSchema. This function only does format validation.
    if (!value) {
      return undefined;
    }
    if (type === FIDES_DATASET_REFERENCE) {
      if (!value.includes(".")) {
        return "Dataset reference must be dot delimited";
      }
      const parts = value.split(".");
      if (parts.length < 3) {
        return "Dataset reference must include at least three parts";
      }
    }
    return undefined;
  };

  const isRequiredField = (key: string): boolean =>
    secretsSchema?.required?.includes(key) ?? false;

  const getFieldValidation = (
    key: string,
    fieldSchema: ConnectionTypeSecretSchemaProperty,
  ) => {
    const refType = fieldSchema.allOf?.[0].$ref;
    if (refType) {
      return (value: string | undefined) =>
        validateField(fieldSchema.title, value, refType);
    }
    return undefined;
  };

  const preprocessValues = (values: Record<string, any>) => {
    const updatedValues = cloneDeep(values);
    if (secretsSchema) {
      Object.keys(secretsSchema.properties).forEach((key) => {
        if (
          secretsSchema.properties[key].allOf?.[0].$ref ===
          FIDES_DATASET_REFERENCE
        ) {
          const referencePath = updatedValues.secrets[key]?.split(".");
          if (referencePath) {
            updatedValues.secrets[key] = {
              dataset: referencePath.shift(),
              field: referencePath.join("."),
              direction: "from",
            };
          }
        }
        if (
          secretsSchema.title === "WebsiteSchema" &&
          secretsSchema.properties[key].title === "URL"
        ) {
          if (
            !updatedValues.secrets[key].startsWith("http://") &&
            !updatedValues.secrets[key].startsWith("https://")
          ) {
            updatedValues.secrets[key] =
              `https://${updatedValues.secrets[key]}`;
          }
        }
        // sending "" when the backend expects an integer will cause an error
        if (secretsSchema.properties[key].type === "integer") {
          if (
            typeof updatedValues.secrets[key] === "string" &&
            updatedValues.secrets[key].trim() === ""
          ) {
            updatedValues.secrets[key] = undefined;
          }
        }
      });
    }
    return updatedValues;
  };

  return {
    validateField,
    isRequiredField,
    getFieldValidation,
    preprocessValues,
  };
};
