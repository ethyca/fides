import { UploadFile } from "fidesui";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { isFieldVisible } from "~/common/visibility";
import { dateFieldValidation } from "~/components/modals/validation";
import { selectUserLocation } from "~/features/consent/consent.slice";
import { CustomConfigField, CustomDateField } from "~/types/config";

interface UseCustomFieldsFormProps {
  customPrivacyRequestFields: Record<string, CustomConfigField>;
  searchParams?: URLSearchParams | null;
}

const DEFAULT_MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

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
  };

  const getValidationSchema = () => {
    const schema = Yup.object({
      ...Object.fromEntries(
        Object.entries(customPrivacyRequestFields)
          .filter(([, field]) => !field.hidden)
          .map(([key, field]) => {
            const { label, required } = field;
            const fieldType = field.field_type;
            const visibilityRules = field.visible_when;
            const isRequired = required !== false;
            const hasVisibilityRules =
              Array.isArray(visibilityRules) && visibilityRules.length > 0;
            const requiredMessage = `${label} is required`;
            // When the field has visibility rules, gate the required check on
            // the current sibling values: invisible ⇒ not required; visible ⇒
            // existing required logic applies.
            const requiredTest = (
              base: Yup.AnySchema,
              isFilled: (v: unknown) => boolean,
            ) =>
              hasVisibilityRules
                ? base.test(
                    "required-when-visible",
                    requiredMessage,
                    function requiredWhenVisible(value) {
                      const parent = (this.parent ?? {}) as Record<
                        string,
                        unknown
                      >;
                      if (
                        !isFieldVisible(
                          { visible_when: visibilityRules },
                          parent,
                        )
                      ) {
                        return true;
                      }
                      if (!isRequired) {
                        return true;
                      }
                      return isFilled(value);
                    },
                  )
                : base;
            if (fieldType === "multiselect" || fieldType === "checkbox_group") {
              const arr = Yup.array();
              if (hasVisibilityRules) {
                return [
                  key,
                  requiredTest(arr, (v) => Array.isArray(v) && v.length > 0),
                ];
              }
              return [
                key,
                isRequired ? arr.min(1, requiredMessage) : arr.notRequired(),
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
            const str = Yup.string();
            if (hasVisibilityRules) {
              return [
                key,
                requiredTest(str, (v) => typeof v === "string" && v.length > 0),
              ];
            }
            if (fieldType === "date") {
              return [
                key,
                dateFieldValidation(
                  field as CustomDateField,
                  label,
                  isRequired,
                ),
              ];
            }
            return [
              key,
              isRequired ? str.required(requiredMessage) : str.notRequired(),
            ];
          }),
      ),
    });

    return schema;
  };

  return { getInitialValues, getValidationSchema };
};
