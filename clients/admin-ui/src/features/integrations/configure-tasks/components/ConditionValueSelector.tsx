import { Dayjs } from "dayjs";
import {
  AntDatePicker as DatePicker,
  AntInput as Input,
  AntRadio as Radio,
  AntSelect as Select,
  iso31661,
  LocationSelect,
} from "fidesui";
import { ChangeEvent } from "react";

import { useGetLocationsRegulationsQuery } from "~/features/locations/locations.slice";
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
 * Handles boolean, date, location, location_country, location_groups, location_regulations, policy, and string field types.
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

  // Fetch locations and regulations data (only when needed)
  const { data: locationsData } = useGetLocationsRegulationsQuery(undefined, {
    skip:
      fieldType !== "location_groups" && fieldType !== "location_regulations",
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
        className="w-full"
        data-testid="value-date-input"
        aria-label="Select date and time"
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
        aria-label="Select a location"
      />
    );
  }

  // Location country input (countries only, no subdivisions)
  if (fieldType === "location_country") {
    return (
      <LocationSelect
        value={value as string | null}
        onChange={onChange}
        placeholder={disabled ? "Not required" : "Select a country"}
        disabled={disabled}
        data-testid="value-location-country-input"
        allowClear
        aria-label="Select a country"
        options={{ countries: iso31661, regions: [] }}
      />
    );
  }

  // Location groups input (single-select for location groups like 'us', 'eea', etc.)
  if (fieldType === "location_groups") {
    const locationGroupOptions =
      locationsData?.location_groups?.map((group) => ({
        label: group.name,
        value: group.id,
      })) ?? [];

    return (
      <Select
        value={value as string}
        onChange={onChange}
        options={locationGroupOptions}
        placeholder={disabled ? "Not required" : "Select a location group"}
        disabled={disabled}
        data-testid="value-location-groups-input"
        allowClear
        showSearch
        aria-label="Select a location group"
        filterOption={(input, option) =>
          (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
        }
      />
    );
  }

  // Location regulations input (single-select for regulations like 'gdpr', 'ccpa', etc.)
  if (fieldType === "location_regulations") {
    const regulationOptions =
      locationsData?.regulations?.map((regulation) => ({
        label: regulation.name,
        value: regulation.id,
      })) ?? [];

    return (
      <Select
        value={value as string}
        onChange={onChange}
        options={regulationOptions}
        placeholder={disabled ? "Not required" : "Select a regulation"}
        disabled={disabled}
        data-testid="value-location-regulations-input"
        allowClear
        showSearch
        aria-label="Select a regulation"
        filterOption={(input, option) =>
          (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
        }
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
      aria-label="Enter condition value"
    />
  );
};
