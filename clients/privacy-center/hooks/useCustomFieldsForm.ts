import { useCallback } from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { selectUserLocation } from "~/features/consent/consent.slice";
import { CustomConfigField } from "~/types/config";

interface UseCustomFieldsFormProps {
  customPrivacyRequestFields: Record<string, CustomConfigField>;
  searchParams?: URLSearchParams | null;
}

/**
 * Build a Yup validation schema for custom fields, filtering out fields that
 * are hidden or not in the applicable set.
 */
export const buildCustomFieldsValidationSchema = (
  fields: Record<string, CustomConfigField>,
  applicableFields?: Set<string>,
) => {
  return Yup.object({
    ...Object.fromEntries(
      Object.entries(fields)
        .filter(([key, field]) => {
          if (field.hidden) {
            return false;
          }
          if (applicableFields && !applicableFields.has(key)) {
            return false;
          }
          return true;
        })
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
};

export const useCustomFieldsForm = ({
  customPrivacyRequestFields,
  searchParams,
}: UseCustomFieldsFormProps) => {
  const userLocation = useAppSelector(selectUserLocation);

  const getInitialValues = useCallback(() => {
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
  }, [customPrivacyRequestFields, searchParams, userLocation?.code]);

  const getValidationSchema = useCallback(
    (applicableFields?: Set<string>) =>
      buildCustomFieldsValidationSchema(
        customPrivacyRequestFields,
        applicableFields,
      ),
    [customPrivacyRequestFields],
  );

  return { getInitialValues, getValidationSchema };
};
