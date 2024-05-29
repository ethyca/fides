import { CheckCircleIcon, Flex, Text, WarningIcon } from "fidesui";

import { formatDate } from "~/features/common/utils";

const ConnectionStatusNotice = ({
  timestamp,
  succeeded,
}: {
  timestamp?: string;
  succeeded?: boolean;
}) => {
  if (!timestamp) {
    return <Text data-testid="connection-status">Connection not tested</Text>;
  }
  const testDate = formatDate(timestamp);
  return succeeded ? (
    <Flex color="green.400" align="center" data-testid="connection-status">
      <CheckCircleIcon mr={2} />
      <Text>Last connected {testDate}</Text>
    </Flex>
  ) : (
    <Flex color="red.400" align="center" data-testid="connection-status">
      <WarningIcon mr={2} />
      <Text>Last connection failed {testDate}</Text>
    </Flex>
  );
};

export default ConnectionStatusNotice;
