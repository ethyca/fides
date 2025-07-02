import { AntSelect, FormErrorMessage, Input } from "fidesui";
import { ReactNode } from "react";

import { MultiselectFieldValue } from "~/types/forms";

// Use compatible interface for existing config types
interface CustomPrivacyRequestField {
  label: string;
  field_type?: "text" | "select" | "multiselect" | null;
  required?: boolean | null;
  options?: string[] | null;
  default_value?: string | string[] | null;
  hidden?: boolean | null;
  query_param_key?: string | null;
}

interface CustomFieldRendererProps {
  field: CustomPrivacyRequestField;
  fieldKey: string;
  value: string | MultiselectFieldValue;
  onChange: (value: string | MultiselectFieldValue) => void;
  onBlur: () => void;
  error?: ReactNode;
}

const CustomFieldRenderer = ({
  field,
  fieldKey,
  value,
  onChange,
  onBlur,
  error,
}: CustomFieldRendererProps) => {
  if (field.field_type === "multiselect" && field.options) {
    return (
      <>
        <AntSelect
          id={fieldKey}
          data-testid={`select-${fieldKey}`}
          mode="multiple"
          placeholder={`Select ${field.label.toLowerCase()}`}
          value={Array.isArray(value) ? value : []}
          onChange={(selectedValues: string[]) => {
            onChange(selectedValues);
          }}
          onBlur={onBlur}
          options={field.options.map((option: string) => ({
            label: option,
            value: option,
          }))}
          style={{ width: "100%" }}
          getPopupContainer={() => document.body}
          dropdownStyle={{
            maxHeight: 400,
            overflow: "auto",
            zIndex: 1500,
          }}
          dropdownClassName="privacy-form-dropdown"
          aria-label={field.label}
          aria-describedby={`${fieldKey}-error`}
          aria-required={field.required !== false}
        />
        {error && (
          <FormErrorMessage id={`${fieldKey}-error`}>{error}</FormErrorMessage>
        )}
      </>
    );
  }

  if (field.field_type === "select" && field.options) {
    return (
      <>
        <AntSelect
          id={fieldKey}
          data-testid={`select-${fieldKey}`}
          placeholder={`Select ${field.label.toLowerCase()}`}
          value={typeof value === "string" ? value : ""}
          onChange={(selectedValue: string) => {
            onChange(selectedValue);
          }}
          onBlur={onBlur}
          options={field.options.map((option: string) => ({
            label: option,
            value: option,
          }))}
          style={{ width: "100%" }}
          getPopupContainer={() => document.body}
          dropdownStyle={{
            maxHeight: 400,
            overflow: "auto",
            zIndex: 1500,
          }}
          dropdownClassName="privacy-form-dropdown"
          allowClear
          aria-label={field.label}
          aria-describedby={`${fieldKey}-error`}
          aria-required={field.required !== false}
        />
        {error && (
          <FormErrorMessage id={`${fieldKey}-error`}>{error}</FormErrorMessage>
        )}
      </>
    );
  }

  return (
    <>
      <Input
        id={fieldKey}
        name={fieldKey}
        placeholder={field.label}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        value={typeof value === "string" ? value : ""}
        aria-label={field.label}
        aria-describedby={`${fieldKey}-error`}
        aria-required={field.required !== false}
      />
      {error && (
        <FormErrorMessage id={`${fieldKey}-error`}>{error}</FormErrorMessage>
      )}
    </>
  );
};

export default CustomFieldRenderer;
