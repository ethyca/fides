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
  // Debug logging
  console.log(`CustomFieldRenderer rendering field ${fieldKey}:`, {
    field,
    value,
    field_type: field.field_type,
    options: field.options,
  });

  if (field.field_type === "multiselect" && field.options) {
    console.log(
      `Rendering multiselect for ${fieldKey} with data-testid="select-${fieldKey}"`,
    );
    return (
      <>
        <AntSelect
          id={fieldKey}
          data-testid={`select-${fieldKey}`}
          mode="multiple"
          placeholder={`Select ${field.label.toLowerCase()}`}
          value={(value as MultiselectFieldValue) || []}
          onChange={(selectedValues: string[]) => {
            console.log(`${fieldKey} multiselect onChange:`, selectedValues);
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
    console.log(
      `Rendering select for ${fieldKey} with data-testid="select-${fieldKey}"`,
    );
    return (
      <>
        <AntSelect
          id={fieldKey}
          data-testid={`select-${fieldKey}`}
          placeholder={`Select ${field.label.toLowerCase()}`}
          value={(value as string) || ""}
          onChange={(selectedValue: string) => {
            console.log(`${fieldKey} select onChange:`, selectedValue);
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

  console.log(`Rendering text input for ${fieldKey}`);
  return (
    <>
      <Input
        id={fieldKey}
        name={fieldKey}
        placeholder={field.label}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        value={value as string}
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
