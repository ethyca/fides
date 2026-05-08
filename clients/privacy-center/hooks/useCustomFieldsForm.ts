import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { selectUserLocation } from "~/features/consent/consent.slice";
import { CustomConfigField, CustomDateField } from "~/types/config";

interface UseCustomFieldsFormProps {
  customPrivacyRequestFields: Record<string, CustomConfigField>;
  searchParams?: URLSearchParams | null;
}

export const useCustomFieldsForm = ({
  customPrivacyRequestFields,
  searchParams,
}: UseCustomFieldsFormProps) => {
  const userLocation = useAppSelector(selectUserLocation);

  const getInitialValues = () => {
    const values = Object.fromEntries(
      Object.entries(customPrivacyRequestFields).map(([key, field]) => {
        const valueFromQueryParam =
          field?.query_param_key &&
          searchParams &&
          searchParams.get(field.query_param_key);

        const defaultLocationValue =
          field?.field_type === "location" && field.ip_geolocation_hint
            ? userLocation?.code
            : null;

        switch (field.field_type) {
          case "multiselect": {
            // Determine the multiselect value with proper precedence
            let value: string[];
            if (valueFromQueryParam) {
              value = [valueFromQueryParam];
            } else if (Array.isArray(field?.default_value)) {
              value = field.default_value;
            } else {
              value = field.default_value ?? [];
            }
            return [key, value];
          }
          case "location":
            return [
              key,
              valueFromQueryParam ||
                field?.default_value ||
                defaultLocationValue ||
                "",
            ];
          default:
            return [key, valueFromQueryParam || field?.default_value || ""];
        }
      }),
    );

    return values;
  };

  const getValidationSchema = () => {
    const schema = Yup.object({
      ...Object.fromEntries(
        Object.entries(customPrivacyRequestFields)
          .filter(([, field]) => !field.hidden)
          .map(([key, field]) => {
            const { label, required, field_type } = field;
            const isRequired = required !== false;
            if (field_type === "multiselect") {
              return [
                key,
                isRequired
                  ? Yup.array().min(1, `${label} is required`)
                  : Yup.array().notRequired(),
              ];
            }
            if (field_type === "date") {
              const dateField = field as CustomDateField;
              let dateSchema = Yup.string().matches(
                /^\d{4}-\d{2}-\d{2}$/,
                `${label} must be a valid date (YYYY-MM-DD)`,
              );
              if (dateField.max) {
                dateSchema = dateSchema.test(
                  "not-after-max",
                  `${label} must be on or before ${dateField.max}`,
                  (v) => !v || v <= dateField.max!,
                );
              }
              if (dateField.min) {
                dateSchema = dateSchema.test(
                  "not-before-min",
                  `${label} must be on or after ${dateField.min}`,
                  (v) => !v || v >= dateField.min!,
                );
              }
              return [
                key,
                isRequired
                  ? dateSchema.required(`${label} is required`)
                  : dateSchema,
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

    return schema;
  };

  return { getInitialValues, getValidationSchema };
};
