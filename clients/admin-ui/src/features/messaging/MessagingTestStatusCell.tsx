import { formatDistance } from "date-fns";
import { AntTag as Tag, AntTooltip as Tooltip } from "fidesui";

import { formatDate } from "~/features/common/utils";
import { MessagingConfigResponse } from "~/types/api";

interface MessagingTestStatusCellProps {
  messagingConfig: MessagingConfigResponse;
}

const MessagingVerificationStatusCell = ({
  messagingConfig,
}: MessagingTestStatusCellProps) => {
  const {
    last_test_succeeded: lastTestSucceeded,
    last_test_timestamp: lastTestTimestamp,
  } = messagingConfig;

  // If no test has been run yet
  if (!lastTestTimestamp) {
    return <Tag>Verify configuration</Tag>;
  }

  const testTime = new Date(lastTestTimestamp);
  const formattedTime = formatDate(testTime);
  const formattedDistance = formatDistance(testTime, new Date(), {
    addSuffix: true,
  });

  return (
    <Tooltip title={`Last verified: ${formattedTime}`}>
      <Tag
        color={lastTestSucceeded ? "success" : "error"}
        data-testid={lastTestSucceeded ? "test-success" : "test-error"}
      >
        {lastTestSucceeded ? "Succeeded" : "Failed"} {formattedDistance}
      </Tag>
    </Tooltip>
  );
};

export default MessagingVerificationStatusCell;
