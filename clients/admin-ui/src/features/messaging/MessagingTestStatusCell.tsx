import { formatDistance } from "date-fns";
import { AntTag as Tag, AntTooltip as Tooltip } from "fidesui";

import { formatDate } from "~/features/common/utils";
import { MessagingConfigResponse } from "~/types/api";

interface MessagingTestStatusCellProps {
  messagingConfig: MessagingConfigResponse;
}

const MessagingTestStatusCell = ({
  messagingConfig,
}: MessagingTestStatusCellProps) => {
  const {
    last_test_succeeded: lastTestSucceeded,
    last_test_timestamp: lastTestTimestamp,
  } = messagingConfig;

  // If no test has been run yet
  if (!lastTestTimestamp) {
    return <Tag>Not tested</Tag>;
  }

  const testTime = new Date(lastTestTimestamp);
  const formattedTime = formatDate(testTime);
  const formattedDistance = formatDistance(testTime, new Date(), {
    addSuffix: true,
  });

  return (
    <Tooltip title={`Last tested: ${formattedTime}`}>
      <Tag
        color={lastTestSucceeded ? "success" : "error"}
        data-testid={lastTestSucceeded ? "test-success" : "test-error"}
      >
        {lastTestSucceeded ? "Success" : "Failed"} {formattedDistance}
      </Tag>
    </Tooltip>
  );
};

export default MessagingTestStatusCell;
