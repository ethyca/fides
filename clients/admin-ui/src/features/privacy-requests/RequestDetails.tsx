import {
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntTooltip as Tooltip,
  AntTypography as Typography,
} from "fidesui";

import ClipboardButton from "~/features/common/ClipboardButton";
import DaysLeftTag from "~/features/common/DaysLeftTag";
import { useFeatures } from "~/features/common/features";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import RequestType from "~/features/common/RequestType";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { PrivacyRequestStatus as ApiPrivacyRequestStatus } from "~/types/api/models/PrivacyRequestStatus";

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
            daysLeft={subjectRequest.days_left}
            includeText
            status={subjectRequest.status as ApiPrivacyRequestStatus}
          />
        </RequestDetailsRow>
        <RequestDetailsRow label="Request type">
          <RequestType rules={policy.rules} />
        </RequestDetailsRow>
        <RequestDetailsRow label="Source">
          {hasPlus && (
            <Typography.Text>{subjectRequest.source || "-"}</Typography.Text>
          )}
        </RequestDetailsRow>

        {Object.entries(identity)
          .filter(([, { value }]) => value !== null)
          .map(([key, { value = "", label }]) => {
            const text = `${value} ${!identityVerifiedAt ? "(Unverified)" : ""}`;

            return (
              <RequestDetailsRow
                label={`Subject ${label.toLocaleLowerCase()}`}
                key={key}
              >
                <Tooltip title={text} trigger="click">
                  <Typography.Text ellipsis>{text}</Typography.Text>
                </Tooltip>
              </RequestDetailsRow>
            );
          })}

        <RequestCustomFields subjectRequest={subjectRequest} />
      </Flex>
      <Form layout="vertical">
        <Form.Item label="Request ID:" className="mb-4">
          <Flex gap={1}>
            <Input readOnly value={id} data-testid="request-detail-value-id" />
            <ClipboardButton copyText={id} size="small" />
          </Flex>
        </Form.Item>
        <Form.Item label="Policy key:" className="mb-4">
          <Input
            readOnly
            value={subjectRequest.policy.key}
            data-testid="request-detail-value-policy"
          />
        </Form.Item>
      </Form>
    </div>
  );
};

export default RequestDetails;
