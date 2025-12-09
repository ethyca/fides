import { Dayjs } from "dayjs";
import {
  AntDatePicker as DatePicker,
  AntInput as Input,
  AntRadio as Radio,
  AntSelect as Select,
  LocationSelect,
} from "fidesui";
import { ChangeEvent } from "react";

import { useGetPoliciesQuery } from "~/features/policy/policy.slice";

import { FieldType } from "../utils";

interface ConditionValueSelectorProps {
  fieldType: FieldType;
  disabled?: boolean;
  value?: string | boolean | Dayjs | null;
  onChange?: (value: string | boolean | Dayjs | null) => void;
}

/**
 * Renders the appropriate input component based on the field type.
 * Handles boolean, date, location, policy, and string field types.
 * This component is designed to work with Ant Design Form.Item.
 */
export const ConditionValueSelector = ({
  fieldType,
  disabled = false,
  value,
  onChange,
}: ConditionValueSelectorProps) => {
  // Fetch policies for policy selector (only when needed)
  const { data: policiesData } = useGetPoliciesQuery(undefined, {
    skip: fieldType !== "policy",
  });

  // Boolean input
  if (fieldType === "boolean") {
    return (
      <Radio.Group
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
        data-testid="value-boolean-input"
      >
        {/* eslint-disable-next-line react/jsx-boolean-value */}
        <Radio value>True</Radio>
        <Radio value={false}>False</Radio>
      </Radio.Group>
    );
  }

  // Date input
  if (fieldType === "date") {
    return (
      <DatePicker
        value={value as Dayjs | null}
        onChange={onChange}
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
        value={value as string | null}
        onChange={onChange}
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
        value={value as string}
        onChange={onChange}
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
      value={value as string}
      onChange={(e: ChangeEvent<HTMLInputElement>) =>
        onChange?.(e.target.value)
      }
      placeholder={
        disabled ? "Not required" : "Enter value (text, number, or true/false)"
      }
      disabled={disabled}
      data-testid="value-input"
    />
  );
};
