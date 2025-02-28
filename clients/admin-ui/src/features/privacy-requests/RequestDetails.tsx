import {
  AntForm as Form,
  AntInput as Input,
  AntTag as Tag,
  AntTypography as Typography,
  Flex,
} from "fidesui";

import ClipboardButton from "~/features/common/ClipboardButton";
import DaysLeftTag from "~/features/common/DaysLeftTag";
import { useFeatures } from "~/features/common/features";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import RequestType from "~/features/common/RequestType";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { PrivacyRequestStatus as ApiPrivacyRequestStatus } from "~/types/api/models/PrivacyRequestStatus";

import ReprocessButton from "./buttons/ReprocessButton";
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
      <div className="mb-6 flex flex-col gap-3">
        <RequestDetailsRow label="Status">
          <Flex>
            <RequestStatusBadge status={status} />
          </Flex>
          <div className="flex gap-3">
            {status === "error" && (
              <ReprocessButton subjectRequest={subjectRequest} />
            )}
          </div>
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
          .map(([key, { value, label }]) => (
            <RequestDetailsRow
              label={`Subject ${label.toLocaleLowerCase()}`}
              key={key}
            >
              <Typography.Text>{value || ""}</Typography.Text>
              <Tag className="ml-1">
                {identityVerifiedAt ? "Verified" : "Unverified"}
              </Tag>
            </RequestDetailsRow>
          ))}
      </div>
      <Form layout="vertical">
        <Form.Item label="Request ID:" className="mb-4">
          <div className="flex gap-1">
            <Input readOnly value={id} />
            <ClipboardButton copyText={id} size="small" />
          </div>
        </Form.Item>
        <Form.Item label="Policy key:" className="mb-4">
          <Input readOnly value={subjectRequest.policy.key} />
        </Form.Item>
      </Form>
    </div>
  );
};

export default RequestDetails;
