import {
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntSpace as Space,
  AntTooltip as Tooltip,
  AntTypography as Typography,
} from "fidesui";

import DaysLeftTag from "~/features/common/DaysLeftTag";
import { useFeatures } from "~/features/common/features";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import RequestType from "~/features/common/RequestType";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { PrivacyRequestStatus as ApiPrivacyRequestStatus } from "~/types/api/models/PrivacyRequestStatus";

import ClipboardButton from "../common/ClipboardButton";
import { renderValue } from "../common/utils";
import RequestAttachments from "./attachments/RequestAttachments";
import RequestCustomFields from "./RequestCustomFields";
import RequestDetailsRow from "./RequestDetailsRow";

type RequestDetailsProps = {
  subjectRequest: PrivacyRequestEntity;
};

const RequestDetails = ({ subjectRequest }: RequestDetailsProps) => {
  const { plus: hasPlus } = useFeatures();
  const {
    id,
    status,
    policy,
    identity,
    identity_verified_at: identityVerifiedAt,
  } = subjectRequest;

  return (
    <div>
      <div className="mb-6">
        <Typography.Title level={2}>Request details</Typography.Title>
      </div>
      <Flex vertical gap={12} className="mb-6">
        <RequestDetailsRow label="Status">
          <RequestStatusBadge status={status} />
        </RequestDetailsRow>
        <RequestDetailsRow label="Time remaining">
          <DaysLeftTag
            daysLeft={subjectRequest.days_left || undefined}
            includeText
            status={subjectRequest.status as ApiPrivacyRequestStatus}
          />
        </RequestDetailsRow>
        <RequestDetailsRow label="Request type">
          {!!policy.rules && <RequestType rules={policy.rules} />}
        </RequestDetailsRow>
        <RequestDetailsRow label="Source">
          {hasPlus && (
            <Typography.Text>{subjectRequest.source || "-"}</Typography.Text>
          )}
        </RequestDetailsRow>

        {
          /*
           * Doing this despite what the api is saying
           * Casting to unknown to cover all bases until types are fixed
           */
          identity &&
            Object.entries(identity as Record<string, unknown>)
              .filter(
                ([, item]) =>
                  item &&
                  typeof item === "object" &&
                  "value" in item &&
                  !!item?.value,
              )
              .map(([key, item]) => {
                const parsedValue =
                  item &&
                  typeof item === "object" &&
                  "value" in item &&
                  "label" in item &&
                  typeof item.label === "string"
                    ? item
                    : null;
                const text = `${renderValue(parsedValue?.value)}${!identityVerifiedAt ? " (Unverified)" : ""}`;
                const label =
                  typeof parsedValue?.label === "string" &&
                  parsedValue.label.toLocaleLowerCase();

                return (
                  <RequestDetailsRow label={`Subject ${label}`} key={key}>
                    <Tooltip title={text} trigger="click">
                      <Typography.Text ellipsis>{text}</Typography.Text>
                    </Tooltip>
                  </RequestDetailsRow>
                );
              })
        }

        <RequestCustomFields subjectRequest={subjectRequest} />
      </Flex>
      <Form layout="vertical">
        <Form.Item label="Request ID:" className="mb-4">
          <Flex gap={1}>
            <Space.Compact style={{ width: "100%" }}>
              <Input
                readOnly
                value={id}
                data-testid="request-detail-value-id"
              />
              <Button icon={<ClipboardButton copyText={id} />} />
            </Space.Compact>
          </Flex>
        </Form.Item>
        <Form.Item label="Policy key:" className="mb-4">
          <Input
            readOnly
            value={subjectRequest.policy.key || undefined}
            data-testid="request-detail-value-policy"
          />
        </Form.Item>
      </Form>
      <RequestAttachments subjectRequest={subjectRequest} />
    </div>
  );
};

export default RequestDetails;
