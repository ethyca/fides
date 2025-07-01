import * as Yup from "yup";

import { FormValues, MultiselectFieldValue } from "~/types/forms";

// Use the existing config types to maintain compatibility
interface CustomPrivacyRequestField {
  label: string;
  field_type?: "text" | "select" | "multiselect" | null;
  required?: boolean | null;
  options?: string[] | null;
  default_value?: string | string[] | null;
  hidden?: boolean | null;
  query_param_key?: string | null;
}

interface UseCustomFieldsFormProps {
  customPrivacyRequestFields: Record<string, CustomPrivacyRequestField>;
  searchParams?: URLSearchParams | null;
}

export const useCustomFieldsForm = ({
  customPrivacyRequestFields,
  searchParams,
}: UseCustomFieldsFormProps) => {
  // Debug logging to understand what we're receiving
  console.log("useCustomFieldsForm received:", customPrivacyRequestFields);

  const getInitialValues = (): FormValues => {
    const values = Object.fromEntries(
      Object.entries(customPrivacyRequestFields)
        .filter(([, field]) => !field.hidden)
        .map(([key, field]) => {
          console.log(`Processing field ${key}:`, field);

          const valueFromQueryParam =
            field.query_param_key &&
            searchParams &&
            searchParams.get(field.query_param_key);

          let value: string | MultiselectFieldValue;
          if (field.field_type === "multiselect") {
            // For multiselect fields, default to empty array or convert to array
            if (valueFromQueryParam) {
              value = [valueFromQueryParam];
            } else if (
              field.default_value &&
              Array.isArray(field.default_value)
            ) {
              value = field.default_value;
            } else if (field.default_value) {
              value = [field.default_value];
            } else {
              value = [];
            }
          } else {
            value = valueFromQueryParam || field.default_value || "";
          }

          console.log(`Field ${key} initial value:`, value);
          return [key, value];
        }),
    );

    console.log("getInitialValues returning:", values);
    return values;
  };

  const getValidationSchema = () => {
    const schema = Yup.object({
      ...Object.fromEntries(
        Object.entries(customPrivacyRequestFields)
          .filter(([, field]) => !field.hidden)
          .map(([key, { label, required, field_type }]) => {
            const isRequired = required !== false;
            if (field_type === "multiselect") {
              return [
                key,
                isRequired
                  ? Yup.array().min(1, `${label} is required`)
                  : Yup.array().notRequired(),
              ];
            }
            return [
              key,
              isRequired
                ? Yup.string().required(`${label} is required`)
                : Yup.string().notRequired(),
            ];
          }),
      ),
    });

    console.log(
      "getValidationSchema returning schema with fields:",
      Object.keys(schema.fields),
    );
    return schema;
  };

  return { getInitialValues, getValidationSchema };
};
