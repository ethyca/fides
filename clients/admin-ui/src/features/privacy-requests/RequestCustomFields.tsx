import { AntTag as Tag, AntTypography as Typography } from "fidesui";

import RequestDetailsRow from "./RequestDetailsRow";
import { PrivacyRequestEntity } from "./types";

type RequestCustomFieldsProps = {
  subjectRequest: PrivacyRequestEntity;
};

const RequestCustomFields = ({ subjectRequest }: RequestCustomFieldsProps) => {
  const { custom_privacy_request_fields: customPrivacyRequestFields } =
    subjectRequest;

  return (
    <div>
      {customPrivacyRequestFields &&
        Object.keys(customPrivacyRequestFields).length > 0 && (
          <>
            <Typography.Title level={5}>Custom request fields</Typography.Title>

            {Object.entries(customPrivacyRequestFields)
              .filter(([, item]) => item.value)
              .map(([key, item]) => (
                <RequestDetailsRow label={item.label} key={key}>
                  <Typography.Text>
                    {Array.isArray(item.value)
                      ? item.value.join(", ")
                      : item.value}
                  </Typography.Text>
                  <Tag className="ml-1">Unverified</Tag>
                </RequestDetailsRow>
              ))}
          </>
        )}
    </div>
  );
};

export default RequestCustomFields;
