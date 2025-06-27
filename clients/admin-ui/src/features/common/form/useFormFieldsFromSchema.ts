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
    let error;
    if (typeof value === "undefined" || value === "" || value === undefined) {
      error = `${label} is required`;
    }
    if (type === FIDES_DATASET_REFERENCE) {
      if (!value?.includes(".")) {
        error = "Dataset reference must be dot delimited";
      } else {
        const parts = value.split(".");
        if (parts.length < 3) {
          error = "Dataset reference must include at least three parts";
        }
      }
    }
    return error;
  };

  const isRequiredField = (key: string): boolean =>
    secretsSchema?.required?.includes(key) ?? false; // ||
  // (secretsSchema?.properties?.[key] !== undefined &&
  //   "default" in secretsSchema.properties[key]);

  const getFieldValidation = (
    key: string,
    fieldSchema: ConnectionTypeSecretSchemaProperty,
  ) => {
    if (isRequiredField(key)) {
      return (value: string | undefined) =>
        validateField(fieldSchema.title, value, fieldSchema.allOf?.[0].$ref);
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
