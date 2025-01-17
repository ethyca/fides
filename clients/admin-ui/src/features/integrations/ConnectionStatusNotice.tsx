import { CheckCircleIcon, Flex, Text, WarningTwoIcon } from "fidesui";

import { formatDate } from "~/features/common/utils";

export type ConnectionStatusData = {
  timestamp?: string | null;
  succeeded?: boolean;
};

const ConnectionStatusNotice = ({
  testData,
}: {
  testData: ConnectionStatusData;
}) => {
  if (!testData.timestamp) {
    return <Text data-testid="connection-status">Connection not tested</Text>;
  }
  const testDate = formatDate(testData.timestamp);
  return testData.succeeded ? (
    <Flex
      color="success-text.900"
      align="center"
      data-testid="connection-status"
    >
      <CheckCircleIcon mr={2} boxSize={4} />
      <Text>Last connected {testDate}</Text>
    </Flex>
  ) : (
    <Flex color="error-text.900" align="center" data-testid="connection-status">
      <WarningTwoIcon mr={2} boxSize={4} />
      <Text>Last connection failed {testDate}</Text>
    </Flex>
  );
};

export default ConnectionStatusNotice;
