import { UploadFile } from "fidesui";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { selectUserLocation } from "~/features/consent/consent.slice";
import { CustomConfigField } from "~/types/config";

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
            const isRequired = required !== false;

            switch (field.field_type) {
              case "multiselect":
              case "checkbox_group":
                return [
                  key,
                  isRequired
                    ? Yup.array().min(1, `${label} is required`)
                    : Yup.array().notRequired(),
                ];
              case "checkbox":
                // Checkbox is always valid — false is a legitimate value
                return [key, Yup.boolean().notRequired()];
              case "file": {
                const maxSize = field.max_size_bytes ?? DEFAULT_MAX_SIZE_BYTES;
                const allowedTypes = field.allowed_mime_types;
                let fileSchema = Yup.array();
                if (isRequired) {
                  fileSchema = fileSchema.min(
                    1,
                    `${label} requires at least one file`,
                  );
                }
                fileSchema = fileSchema.test(
                  "file-size",
                  `Each file must be under ${Math.round(maxSize / (1024 * 1024))}MB`,
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
                        (f) => !f.type || allowedTypes.includes(f.type),
                      );
                    },
                  );
                }
                return [key, fileSchema];
              }
              default:
                return [
                  key,
                  isRequired
                    ? Yup.string().required(`${label} is required`)
                    : Yup.string().notRequired(),
                ];
            }
          }),
      ),
    });

    return schema;
  };

  return { getInitialValues, getValidationSchema };
};
