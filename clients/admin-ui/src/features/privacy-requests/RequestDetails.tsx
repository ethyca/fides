import {
  AntForm as Form,
  AntInput as Input,
  AntTypography as Typography,
  Flex,
} from "fidesui";

import ClipboardButton from "~/features/common/ClipboardButton";
import DaysLeftTag from "~/features/common/DaysLeftTag";
import { useFeatures } from "~/features/common/features";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import RequestType, { getActionTypes } from "~/features/common/RequestType";
import DownloadAccessResults from "~/features/privacy-requests/DownloadAccessResults";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { ActionType } from "~/types/api";
import { PrivacyRequestStatus as ApiPrivacyRequestStatus } from "~/types/api/models/PrivacyRequestStatus";

import ApproveButton from "./buttons/ApproveButton";
import DenyButton from "./buttons/DenyButton";
import ReprocessButton from "./buttons/ReprocessButton";
import RequestDetailsRow from "./RequestDetailsRow";

type RequestDetailsProps = {
  subjectRequest: PrivacyRequestEntity;
};

const RequestDetails = ({ subjectRequest }: RequestDetailsProps) => {
  const { plus: hasPlus } = useFeatures();
  const { id, status, policy } = subjectRequest;

  const {
    flags: { downloadAccessRequestResults },
  } = useFeatures();

  const showDownloadResults =
    downloadAccessRequestResults &&
    getActionTypes(policy.rules).includes(ActionType.ACCESS) &&
    status === ApiPrivacyRequestStatus.COMPLETE;

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

            {status === "pending" && (
              <>
                <ApproveButton subjectRequest={subjectRequest}>
                  Approve
                </ApproveButton>
                <DenyButton subjectRequest={subjectRequest}>Deny</DenyButton>
              </>
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
      {showDownloadResults && <DownloadAccessResults requestId={id} />}
    </div>
  );
};

export default RequestDetails;
