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
  const { label, field_type, options } = fieldDefinition;

  // Skip location fields - not implemented yet
  if (field_type === "location") {
    return null;
  }

  // For select and multiselect, render a single Select component
  if (field_type === "select" || field_type === "multiselect") {
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

  // Default to text input for text or undefined field_type
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
