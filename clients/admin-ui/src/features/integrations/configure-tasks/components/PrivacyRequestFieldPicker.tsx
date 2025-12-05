import {
  AntSelect as Select,
  AntTypography as Typography,
  Flex,
} from "fidesui";
import { useMemo } from "react";

import { useGetPrivacyRequestFieldsQuery } from "~/features/datastore-connections/connection-manual-tasks.slice";
import { extractUniqueCustomFields } from "~/features/privacy-requests/dashboard/utils";
import { useGetPrivacyCenterConfigQuery } from "~/features/privacy-requests/privacy-requests.slice";

import {
  ALLOWED_PRIVACY_REQUEST_FIELDS,
  flattenPrivacyRequestFields,
  groupFieldsByCategory,
} from "../utils";

interface PrivacyRequestFieldPickerProps {
  value?: string;
  onChange?: (value: string | undefined) => void;
  connectionKey: string;
  disabled?: boolean;
}

export const PrivacyRequestFieldPicker = ({
  value,
  onChange,
  connectionKey,
  disabled = false,
}: PrivacyRequestFieldPickerProps) => {
  const { data, isLoading, error } = useGetPrivacyRequestFieldsQuery({
    connectionKey,
  });

  // Fetch privacy center config to get custom fields
  const { data: privacyCenterConfig } = useGetPrivacyCenterConfigQuery();

  // Flatten the nested structure and filter to allowed fields
  const fieldOptions = useMemo(() => {
    if (!data?.privacy_request) {
      return [];
    }

    const flattenedFields = flattenPrivacyRequestFields(
      data.privacy_request as Record<string, unknown>,
      ALLOWED_PRIVACY_REQUEST_FIELDS,
    );

    const standardFieldOptions = groupFieldsByCategory(flattenedFields);

    // Extract unique custom fields from privacy center config
    const uniqueCustomFields = extractUniqueCustomFields(
      privacyCenterConfig?.actions,
    );

    // Transform custom fields to field options
    const customFieldOptions = Object.entries(uniqueCustomFields).map(
      ([fieldName, fieldDefinition]) => ({
        label: fieldDefinition.label,
        value: `privacy_request.custom_privacy_request_fields.${fieldName}`,
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
  }, [data, privacyCenterConfig]);

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
