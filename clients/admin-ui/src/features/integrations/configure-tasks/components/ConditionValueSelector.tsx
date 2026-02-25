import dayjs, { Dayjs } from "dayjs";
import {
  DatePicker,
  Input,
  iso31661,
  LocationSelect,
  Radio,
  Select,
} from "fidesui";
import { ChangeEvent } from "react";

import { useGetLocationsRegulationsQuery } from "~/features/locations/locations.slice";
import { useGetPoliciesQuery } from "~/features/policies/policy.slice";
import { Operator } from "~/types/api";

import { CustomFieldMetadata } from "../types";
import { FieldType, getFieldTypeWithMetadata } from "../utils";

interface ConditionValueSelectorProps {
  fieldType: FieldType;
  disabled?: boolean;
  value?: string | boolean | Dayjs | string[] | null;
  onChange?: (value: string | boolean | Dayjs | string[] | null) => void;
  fieldAddress?: string;
  customFieldMetadata?: CustomFieldMetadata | null;
  operator?: Operator;
}

/**
 * Renders the appropriate input component based on the field type.
 * Handles boolean, date, location, location_country, location_groups, location_regulations,
 * policy, custom_select, custom_multiselect, and string field types.
 * This component is designed to work with Ant Design Form.Item.
 */
export const ConditionValueSelector = ({
  fieldType: baseFieldType,
  disabled = false,
  value,
  onChange,
  fieldAddress,
  customFieldMetadata,
  operator,
}: ConditionValueSelectorProps) => {
  const isMultiSelect = operator === Operator.LIST_CONTAINS;

  const fieldType = fieldAddress
    ? getFieldTypeWithMetadata(fieldAddress, customFieldMetadata ?? null)
    : baseFieldType;

  const { data: policiesData } = useGetPoliciesQuery(undefined, {
    skip: baseFieldType !== "policy",
  });

  const { data: locationsData } = useGetLocationsRegulationsQuery(undefined, {
    skip:
      fieldType !== "location_groups" && fieldType !== "location_regulations",
  });

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

  if (fieldType === "date") {
    const dateValue = dayjs.isDayjs(value) ? value : null;

    return (
      <DatePicker
        value={dateValue}
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

  if (fieldType === "location") {
    const label = isMultiSelect ? "Select locations" : "Select a location";
    const sharedProps = {
      onChange,
      placeholder: disabled ? "Not required" : label,
      disabled,
      "data-testid": "value-location-input",
      allowClear: true,
      "aria-label": label,
    };
    return isMultiSelect ? (
      <LocationSelect mode="multiple" value={value as string[]} {...sharedProps} />
    ) : (
      <LocationSelect value={value as string | null} {...sharedProps} />
    );
  }

  if (fieldType === "location_country") {
    const label = isMultiSelect ? "Select countries" : "Select a country";
    const sharedProps = {
      onChange,
      placeholder: disabled ? "Not required" : label,
      disabled,
      "data-testid": "value-location-country-input",
      allowClear: true,
      "aria-label": label,
      options: { countries: iso31661, regions: [] },
    };
    return isMultiSelect ? (
      <LocationSelect mode="multiple" value={value as string[]} {...sharedProps} />
    ) : (
      <LocationSelect value={value as string | null} {...sharedProps} />
    );
  }

  if (fieldType === "location_groups") {
    const locationGroupOptions =
      locationsData?.location_groups?.map((group) => ({
        label: group.name,
        value: group.id,
      })) ?? [];
    const label = isMultiSelect ? "Select location groups" : "Select a location group";
    const sharedProps = {
      onChange,
      options: locationGroupOptions,
      placeholder: disabled ? "Not required" : label,
      disabled,
      "data-testid": "value-location-groups-input",
      allowClear: true,
      showSearch: true,
      "aria-label": label,
      filterOption: (input: string, option: { label?: string } | undefined) =>
        (option?.label ?? "").toLowerCase().includes(input.toLowerCase()),
    };
    return isMultiSelect ? (
      <Select mode="multiple" value={value as string[]} {...sharedProps} />
    ) : (
      <Select value={value as string} {...sharedProps} />
    );
  }

  if (fieldType === "location_regulations") {
    const regulationOptions =
      locationsData?.regulations?.map((regulation) => ({
        label: regulation.name,
        value: regulation.id,
      })) ?? [];
    const label = isMultiSelect ? "Select regulations" : "Select a regulation";
    const sharedProps = {
      onChange,
      options: regulationOptions,
      placeholder: disabled ? "Not required" : label,
      disabled,
      "data-testid": "value-location-regulations-input",
      allowClear: true,
      showSearch: true,
      "aria-label": label,
      filterOption: (input: string, option: { label?: string } | undefined) =>
        (option?.label ?? "").toLowerCase().includes(input.toLowerCase()),
    };
    return isMultiSelect ? (
      <Select mode="multiple" value={value as string[]} {...sharedProps} />
    ) : (
      <Select value={value as string} {...sharedProps} />
    );
  }

  if (fieldType === "policy") {
    const policyOptions =
      policiesData?.items.map((policy) => ({
        label: policy.name,
        value: policy.key,
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

  // Custom select/multiselect input (single-select for conditions)
  // Even for multiselect fields, conditions compare against a single value
  if (
    (fieldType === "custom_select" || fieldType === "custom_multiselect") &&
    customFieldMetadata?.options
  ) {
    const selectOptions =
      customFieldMetadata.options.map((option) => ({
        label: option,
        value: option,
      })) ?? [];

    return (
      <Select
        value={value as string}
        onChange={onChange}
        options={selectOptions}
        placeholder={
          disabled ? "Not required" : `Select ${customFieldMetadata.label}`
        }
        disabled={disabled}
        data-testid="value-custom-select-input"
        allowClear
        showSearch
        aria-label={`Select ${customFieldMetadata.label}`}
        filterOption={(input, option) =>
          (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
        }
      />
    );
  }

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
