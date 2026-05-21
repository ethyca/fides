import { Typography } from "fidesui";

import { formatIsoDate } from "~/features/common/utils";

import RequestDetailsRow from "./RequestDetailsRow";
import { PrivacyRequestEntity } from "./types";

type RequestCustomFieldsProps = {
  subjectRequest: PrivacyRequestEntity;
};

const formatFieldValue = (value: unknown): string => {
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return formatIsoDate(value);
};

const hasValue = (value: unknown): boolean => {
  if (typeof value === "boolean") {
    return true;
  }
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  return value !== null && value !== undefined && value !== "" && value !== 0;
};

const RequestCustomFields = ({ subjectRequest }: RequestCustomFieldsProps) => {
  const { custom_privacy_request_fields: customPrivacyRequestFields } =
    subjectRequest;

  return (
    <div className="flex flex-col gap-2">
      {customPrivacyRequestFields &&
        Object.keys(customPrivacyRequestFields).length > 0 &&
        Object.entries(customPrivacyRequestFields)
          .filter(([, item]) => hasValue(item.value))
          .map(([key, item]) => (
            <RequestDetailsRow label={item.label} key={key}>
              <Typography.Text>{formatFieldValue(item.value)}</Typography.Text>
            </RequestDetailsRow>
          ))}
    </div>
  );
};

export default RequestCustomFields;
