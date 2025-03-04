import { AntTypography as Typography } from "fidesui";

import RequestDetailsRow from "./RequestDetailsRow";
import { PrivacyRequestEntity } from "./types";

type RequestCustomFieldsProps = {
  subjectRequest: PrivacyRequestEntity;
};

const RequestCustomFields = ({ subjectRequest }: RequestCustomFieldsProps) => {
  const { custom_privacy_request_fields: customPrivacyRequestFields } =
    subjectRequest;

  return (
    <div className="flex flex-col gap-2">
      {customPrivacyRequestFields &&
        Object.keys(customPrivacyRequestFields).length > 0 &&
        Object.entries(customPrivacyRequestFields)
          .filter(([, item]) => item.value)
          .map(([key, item]) => (
            <RequestDetailsRow label={item.label} key={key}>
              <Typography.Text>
                {Array.isArray(item.value) ? item.value.join(", ") : item.value}
              </Typography.Text>
            </RequestDetailsRow>
          ))}
    </div>
  );
};

export default RequestCustomFields;
