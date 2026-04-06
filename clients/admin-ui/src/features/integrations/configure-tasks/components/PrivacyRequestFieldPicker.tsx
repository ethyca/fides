import { ChakraFlex as Flex, Input, Select, Typography } from "fidesui";
import { useCallback, useMemo } from "react";

import { useGetPrivacyRequestFieldsQuery } from "~/features/datastore-connections/connection-manual-tasks.slice";

import { useCustomFieldMetadata } from "../hooks/useCustomFieldMetadata";
import {
  ALLOWED_PRIVACY_REQUEST_FIELDS,
  CONSENT_ALLOWED_PRIVACY_REQUEST_FIELDS,
  CUSTOM_IDENTITY_MANUAL_ENTRY,
  extractCustomIdentityFields,
  flattenPrivacyRequestFields,
  formatFieldLabel,
  groupFieldsByCategory,
  PrivacyRequestField,
  STANDARD_IDENTITY_FIELDS,
} from "../utils";

interface PrivacyRequestFieldPickerProps {
  value?: string;
  onChange?: (value: string | undefined) => void;
  connectionKey: string;
  disabled?: boolean;
  /**
   * When true, filters out fields that are not available for consent requests.
   * This should be set when only consent manual tasks are configured.
   */
  isConsentOnly?: boolean;
}

/**
 * Check if a field address is a custom identity (under identity.* but not a standard one).
 */
const isCustomIdentityValue = (fieldAddress?: string): boolean => {
  if (!fieldAddress) {
    return false;
  }
  return (
    fieldAddress.startsWith(PrivacyRequestField.IDENTITY_PREFIX) &&
    !STANDARD_IDENTITY_FIELDS.has(fieldAddress)
  );
};

export const PrivacyRequestFieldPicker = ({
  value,
  onChange,
  connectionKey,
  disabled = false,
  isConsentOnly = false,
}: PrivacyRequestFieldPickerProps) => {
  const { data, isLoading, error } = useGetPrivacyRequestFieldsQuery({
    connectionKey,
  });

  // Get custom fields from the hook
  const { customFieldsMap } = useCustomFieldMetadata();

  // Flatten the nested structure and filter to allowed fields
  // Use consent-specific allowlist when only consent tasks are configured
  const fieldOptions = useMemo(() => {
    if (!data?.privacy_request) {
      return [];
    }

    const allowedFields = isConsentOnly
      ? CONSENT_ALLOWED_PRIVACY_REQUEST_FIELDS
      : ALLOWED_PRIVACY_REQUEST_FIELDS;

    const flattenedFields = flattenPrivacyRequestFields(
      data.privacy_request as Record<string, unknown>,
      allowedFields,
    );

    const standardFieldOptions = groupFieldsByCategory(flattenedFields);

    // Transform custom fields to field options
    const customFieldOptions = Object.entries(customFieldsMap).map(
      ([fieldName, fieldDefinition]) => ({
        label: fieldDefinition.label,
        value: `${PrivacyRequestField.CUSTOM_FIELDS_PREFIX}${fieldName}`,
      }),
    );

    // If there are custom fields, add them as a separate group
    if (customFieldOptions.length > 0) {
      standardFieldOptions.push({
        label: "Custom fields",
        options: customFieldOptions.sort((a, b) =>
          a.label.localeCompare(b.label),
        ),
      });
    }

    // Extract custom identity fields from the API response
    const customIdentityFields = extractCustomIdentityFields(
      data.privacy_request as Record<string, unknown>,
    );

    const customIdentityOptions = customIdentityFields.map((field) => ({
      label: formatFieldLabel(field.field_path),
      value: field.field_path,
    }));

    // Always include the manual entry option in the custom identities group
    const manualEntryOption = {
      label: "Other (enter custom key)",
      value: CUSTOM_IDENTITY_MANUAL_ENTRY,
    };

    const allCustomIdentityOptions = [
      ...customIdentityOptions.sort((a, b) => a.label.localeCompare(b.label)),
      manualEntryOption,
    ];

    standardFieldOptions.push({
      label: "Custom identities",
      options: allCustomIdentityOptions,
    });

    return standardFieldOptions;
  }, [data, customFieldsMap, isConsentOnly]);

  // Determine if the manual identity key input should be shown:
  // - The user selected "Other (enter custom key)" from the dropdown
  // - Or the current value is a custom identity not present in the known options (editing mode)
  const isManualEntrySelected = value === CUSTOM_IDENTITY_MANUAL_ENTRY;
  const isValueUnknownCustomIdentity = useMemo(() => {
    if (!value || !isCustomIdentityValue(value)) {
      return false;
    }
    const allValues = fieldOptions.flatMap((group) =>
      group.options.map((opt) => opt.value),
    );
    return !allValues.includes(value);
  }, [value, fieldOptions]);

  const showManualKeyInput =
    isManualEntrySelected || isValueUnknownCustomIdentity;

  // The value to display in the select: when the user has typed a manual key,
  // show the sentinel so the select stays on "Other (enter custom key)".
  // When editing an unknown custom identity, also show the sentinel.
  const selectDisplayValue =
    isValueUnknownCustomIdentity || isManualEntrySelected
      ? CUSTOM_IDENTITY_MANUAL_ENTRY
      : value;

  // The key currently in the manual input
  const getManualKeyValue = (): string => {
    if (!value) {
      return "";
    }
    const v = value as string;
    if (isValueUnknownCustomIdentity) {
      return v.replace(PrivacyRequestField.IDENTITY_PREFIX, "");
    }
    if (
      isManualEntrySelected &&
      v !== CUSTOM_IDENTITY_MANUAL_ENTRY &&
      v.startsWith(PrivacyRequestField.IDENTITY_PREFIX)
    ) {
      return v.replace(PrivacyRequestField.IDENTITY_PREFIX, "");
    }
    return "";
  };
  const manualKeyValue = getManualKeyValue();

  const handleSelectChange = useCallback(
    (selectedValue: string | undefined) => {
      if (selectedValue === CUSTOM_IDENTITY_MANUAL_ENTRY) {
        // Set the sentinel as value so the form knows manual entry is active,
        // but don't propagate a real field address yet.
        onChange?.(CUSTOM_IDENTITY_MANUAL_ENTRY);
        return;
      }
      onChange?.(selectedValue);
    },
    [onChange],
  );

  const handleManualKeyChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const rawValue = e.target.value;
      if (rawValue) {
        onChange?.(`${PrivacyRequestField.IDENTITY_PREFIX}${rawValue}`);
      } else {
        // Keep the sentinel so the input stays visible
        onChange?.(CUSTOM_IDENTITY_MANUAL_ENTRY);
      }
    },
    [onChange],
  );

  if (error) {
    return (
      <Flex className="py-2">
        <Typography.Text type="danger">
          Failed to load privacy request fields. Please try again.
        </Typography.Text>
      </Flex>
    );
  }

  if (!isLoading && fieldOptions.length === 0) {
    return (
      <Flex className="py-2">
        <Typography.Text type="secondary">
          No privacy request fields available.
        </Typography.Text>
      </Flex>
    );
  }

  return (
    <Flex direction="column" gap={2}>
      <Select
        value={selectDisplayValue}
        onChange={handleSelectChange}
        options={fieldOptions}
        placeholder="Select a privacy request field"
        aria-label="Select a privacy request field"
        disabled={disabled}
        loading={isLoading}
        allowClear
        showSearch
        optionFilterProp="label"
        data-testid="privacy-request-field-select"
      />
      {showManualKeyInput && (
        <Input
          addonBefore="privacy_request.identity."
          value={manualKeyValue}
          onChange={handleManualKeyChange}
          placeholder="e.g. customer_id"
          disabled={disabled}
          data-testid="manual-identity-key-input"
          autoFocus
        />
      )}
    </Flex>
  );
};
