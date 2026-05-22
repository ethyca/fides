import { UploadFile } from "fidesui";
import { useCallback } from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { dateFieldValidation } from "~/components/modals/validation";
import { selectUserLocation } from "~/features/consent/consent.slice";
import { CustomConfigField, CustomDateField } from "~/types/config";

interface UseCustomFieldsFormProps {
  customPrivacyRequestFields: Record<string, CustomConfigField>;
  searchParams?: URLSearchParams | null;
}

const DEFAULT_MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

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
        .map(([key, field]) => {
          const { label, required, field_type: fieldType } = field;
          const isRequired = required !== false;
          const requiredMessage = `${label} is required`;
          if (fieldType === "multiselect" || fieldType === "checkbox_group") {
            return [
              key,
              isRequired
                ? Yup.array().min(1, requiredMessage)
                : Yup.array().notRequired(),
            ];
          }
          if (fieldType === "checkbox") {
            return [
              key,
              isRequired
                ? Yup.boolean().oneOf([true], requiredMessage)
                : Yup.boolean().notRequired(),
            ];
          }
          if (fieldType === "file") {
            const maxSize = field.max_size_bytes ?? DEFAULT_MAX_SIZE_BYTES;
            const allowedTypes = field.allowed_file_types;
            let fileSchema = Yup.array();
            if (isRequired) {
              fileSchema = fileSchema.min(
                1,
                `${label} requires at least one file`,
              );
            }
            fileSchema = fileSchema.test(
              "file-size",
              `Each file must be under ${Math.ceil(maxSize / (1024 * 1024))}MB`,
              (files) => {
                if (!files) {
                  return true;
                }
                return (files as UploadFile[]).every(
                  (f) => !f.size || f.size <= maxSize,
                );
              },
            );
            if (allowedTypes && allowedTypes.length > 0) {
              fileSchema = fileSchema.test(
                "file-type",
                `Allowed file types: ${allowedTypes.join(", ")}`,
                (files) => {
                  if (!files) {
                    return true;
                  }
                  return (files as UploadFile[]).every(
                    (f) => !!f.type && allowedTypes.includes(f.type),
                  );
                },
              );
            }
            return [key, fileSchema];
          }
          if (fieldType === "date") {
            return [
              key,
              dateFieldValidation(field as CustomDateField, label, isRequired),
            ];
          }
          return [
            key,
            isRequired
              ? Yup.string().required(requiredMessage)
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
          case "multiselect":
          case "checkbox_group": {
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
          case "checkbox":
            return [key, field?.default_value === "true"];
          case "file":
            return [key, [] as UploadFile[]];
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
