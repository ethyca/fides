import { UploadFile } from "fidesui";
import type { FormikErrors, FormikTouched } from "formik";

import { CustomConfigField } from "~/types/config";
import { FormFieldValue, FormValues } from "~/types/forms";

import type { CustomFieldRendererProps } from "./CustomFieldRenderer";

interface FieldFormContext {
  setFieldValue: (field: string, value: unknown) => void;
  handleBlur: (e: { target: { name: string } }) => void;
  touched: FormikTouched<FormValues>;
  errors: FormikErrors<FormValues>;
}

export const buildCustomFieldProps = (
  key: string,
  value: FormFieldValue,
  fieldConfig: CustomConfigField,
  { setFieldValue, handleBlur, touched, errors }: FieldFormContext,
): CustomFieldRendererProps => {
  const sharedProps = {
    fieldKey: key,
    onBlur: () => handleBlur({ target: { name: key } }),
    error: touched[key] && errors[key] ? (errors[key] as string) : undefined,
  };

  switch (fieldConfig.field_type) {
    case "multiselect":
    case "checkbox_group": {
      let arrayValue: string[];
      if (typeof value === "string") {
        arrayValue = [value];
      } else if (Array.isArray(value)) {
        arrayValue = value as string[];
      } else {
        arrayValue = [];
      }
      return {
        ...fieldConfig,
        ...sharedProps,
        value: arrayValue,
        onChange: (v: Array<string>) => setFieldValue(key, v),
      };
    }
    case "checkbox":
      return {
        ...fieldConfig,
        ...sharedProps,
        value: Boolean(value),
        onChange: (v: boolean) => setFieldValue(key, v),
      };
    case "file":
      return {
        ...fieldConfig,
        ...sharedProps,
        value: Array.isArray(value) ? (value as UploadFile[]) : [],
        onChange: (fileList: UploadFile[]) => setFieldValue(key, fileList),
      };
    case "textarea":
      return {
        ...fieldConfig,
        ...sharedProps,
        value: typeof value === "string" ? value : "",
        onChange: (v: string) => setFieldValue(key, v),
      };
    default: {
      let stringValue: string;
      if (typeof value === "string") {
        stringValue = value;
      } else if (Array.isArray(value) && value.length > 0) {
        stringValue = value[0] as string;
      } else {
        stringValue = "";
      }
      return {
        ...fieldConfig,
        ...sharedProps,
        value: stringValue,
        onChange: (v: string) => setFieldValue(key, v),
      };
    }
  }
};
