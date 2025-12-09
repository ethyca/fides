import {
  AntDatePicker as DatePicker,
  AntInput as Input,
  AntRadio as Radio,
  AntSelect as Select,
  LocationSelect,
} from "fidesui";

import { useGetPoliciesQuery } from "~/features/policy/policy.slice";

import { FieldType } from "../utils";

interface ConditionValueSelectorProps {
  fieldType: FieldType;
  disabled?: boolean;
}

/**
 * Renders the appropriate input component based on the field type.
 * Handles boolean, date, location, policy, and string field types.
 */
export const ConditionValueSelector = ({
  fieldType,
  disabled = false,
}: ConditionValueSelectorProps) => {
  // Fetch policies for policy selector
  const { data: policiesData } = useGetPoliciesQuery();

  // Boolean input
  if (fieldType === "boolean") {
    return (
      <Radio.Group disabled={disabled} data-testid="value-boolean-input">
        <Radio value>True</Radio>
        <Radio value={false}>False</Radio>
      </Radio.Group>
    );
  }

  // Date input
  if (fieldType === "date") {
    return (
      <DatePicker
        showTime
        format="YYYY-MM-DD HH:mm:ss"
        placeholder={disabled ? "Not required" : "Select date and time"}
        disabled={disabled}
        style={{ width: "100%" }}
        data-testid="value-date-input"
      />
    );
  }

  // Location input
  if (fieldType === "location") {
    return (
      <LocationSelect
        placeholder={disabled ? "Not required" : "Select a location"}
        disabled={disabled}
        data-testid="value-location-input"
        allowClear
      />
    );
  }

  // Policy input
  if (fieldType === "policy") {
    const policyOptions =
      policiesData?.items.map((policy) => ({
        label: policy.name,
        value: policy.key || policy.name,
      })) ?? [];

    return (
      <Select
        options={policyOptions}
        placeholder={disabled ? "Not required" : "Select a policy"}
        disabled={disabled}
        data-testid="value-policy-input"
        allowClear
        showSearch
        aria-label="Select a policy"
        filterOption={(input, option) =>
          (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
        }
      />
    );
  }

  // Default: string input
  return (
    <Input
      placeholder={
        disabled ? "Not required" : "Enter value (text, number, or true/false)"
      }
      disabled={disabled}
      data-testid="value-input"
    />
  );
};
