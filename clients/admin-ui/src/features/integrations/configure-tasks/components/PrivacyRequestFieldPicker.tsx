import { AntSelect as Select, AntTypography as Typography } from "fidesui";
import { useMemo } from "react";

import { useGetPrivacyRequestFieldsQuery } from "~/features/datastore-connections/connection-manual-tasks.slice";

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

  // Flatten the nested structure and filter to allowed fields
  const fieldOptions = useMemo(() => {
    if (!data?.privacy_request) {
      return [];
    }

    const flattenedFields = flattenPrivacyRequestFields(
      data.privacy_request,
      ALLOWED_PRIVACY_REQUEST_FIELDS,
    );

    return groupFieldsByCategory(flattenedFields);
  }, [data]);

  if (error) {
    return (
      <div className="py-2">
        <Typography.Text type="danger">
          Failed to load privacy request fields. Please try again.
        </Typography.Text>
      </div>
    );
  }

  if (!isLoading && fieldOptions.length === 0) {
    return (
      <div className="py-2">
        <Typography.Text type="secondary">
          No privacy request fields available.
        </Typography.Text>
      </div>
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
      style={{ width: "100%" }}
      data-testid="privacy-request-field-select"
    />
  );
};
