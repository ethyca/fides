import { AntInput as Input, AntSelect as Select } from "fidesui";

// Extended type to include field_type and options that are in the backend but may not be in auto-generated types yet
export interface CustomFieldDefinition {
  label: string;
  field_type?: "text" | "select" | "multiselect" | "location" | null;
  options?: string[] | null;
  required?: boolean | null;
  default_value?: string | string[] | null;
  hidden?: boolean | null;
}

interface CustomFieldFilterProps {
  fieldName: string;
  fieldDefinition: CustomFieldDefinition;
  value: string | null;
  onChange: (value: string | null) => void;
}

export const CustomFieldFilter = ({
  fieldName,
  fieldDefinition,
  value,
  onChange,
}: CustomFieldFilterProps) => {
  const { label, field_type: fieldType, options } = fieldDefinition;

  // Skip location fields - not implemented yet
  if (fieldType === "location") {
    return null;
  }

  // Skip multiselect fields - backend filtering doesn't support array values.
  // The backend explicitly filters out list values in the query logic
  // (see src/fides/api/api/v1/endpoints/privacy_request_endpoints.py:611)
  // because array values are not indexed for searching.
  if (fieldType === "multiselect") {
    return null;
  }

  // For select fields, render a single Select component
  if (fieldType === "select") {
    const selectOptions =
      options?.map((opt) => ({
        label: opt,
        value: opt,
      })) ?? [];

    return (
      <Select
        placeholder={label}
        options={selectOptions}
        value={value || undefined}
        onChange={(selectedValue: string) => {
          onChange(selectedValue || null);
        }}
        allowClear
        data-testid={`custom-field-filter-${fieldName}`}
        aria-label={label}
        className="w-44"
      />
    );
  }

  // Default to text input for text or undefined fieldType
  return (
    <Input
      placeholder={label}
      value={value || ""}
      onChange={(e) => onChange(e.target.value || null)}
      allowClear
      data-testid={`custom-field-filter-${fieldName}`}
      aria-label={label}
      className="w-44"
    />
  );
};
