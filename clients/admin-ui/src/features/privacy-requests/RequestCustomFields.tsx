import { AntTypography as Typography } from "fidesui";

import { renderValue } from "../common/utils";
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
          /*
           * All of these checks are because of poor types exposed on the backend.
           * If there is supposed to be "item" and "value" properties on a returned object, define it.
           */
          .filter(
            ([, item]) =>
              item && typeof item === "object" && "value" in item && item.value,
          )
          .map(
            ([key, item]) =>
              item &&
              typeof item === "object" &&
              "value" in item &&
              "label" in item &&
              typeof item.label === "string" && (
                <RequestDetailsRow label={item?.label} key={key}>
                  <Typography.Text>{renderValue(item.value)}</Typography.Text>
                </RequestDetailsRow>
              ),
          )}
    </div>
  );
};

export default RequestCustomFields;
