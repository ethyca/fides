import { ChakraFlex as Flex, Select, Typography } from "fidesui";
import { useMemo } from "react";

import { useGetPrivacyRequestFieldsQuery } from "~/features/datastore-connections/connection-manual-tasks.slice";

import { useCustomFieldMetadata } from "../hooks/useCustomFieldMetadata";
import {
  ALLOWED_PRIVACY_REQUEST_FIELDS,
  CONSENT_ALLOWED_PRIVACY_REQUEST_FIELDS,
  flattenPrivacyRequestFields,
  groupFieldsByCategory,
  PrivacyRequestField,
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
      return [
        ...standardFieldOptions,
        {
          label: "Custom fields",
          options: customFieldOptions.sort((a, b) =>
            a.label.localeCompare(b.label),
          ),
        },
      ];
    }

    return standardFieldOptions;
  }, [data, customFieldsMap, isConsentOnly]);

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
    <Select
      value={value}
      onChange={onChange}
      options={fieldOptions}
      placeholder="Select a privacy request field"
      aria-label="Select a privacy request field"
      disabled={disabled}
      loading={isLoading}
      allowClear
      showSearch
      data-testid="privacy-request-field-select"
    />
  );
};
