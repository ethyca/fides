import * as Yup from "yup";
import { CustomConfigField } from "~/types/config";
import { useAppSelector } from "~/app/hooks";
import { selectUserLocation } from "~/features/consent/consent.slice";

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
      Object.entries(customPrivacyRequestFields)
        .filter(([, field]) => !field?.hidden)
        .map(([key, field]) => {
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
              const value =
                [valueFromQueryParam] || Array.isArray(field?.default_value)
                  ? field.default_value
                  : (field.default_value ?? []);
              return [key, value];
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

    return schema;
  };

  return { getInitialValues, getValidationSchema };
};
