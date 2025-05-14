import { CheckCircleIcon, Flex, Text, WarningTwoIcon } from "fidesui";

import { formatDate } from "~/features/common/utils";
import { ConnectionSystemTypeMap } from "~/types/api";

export type ConnectionStatusData = {
  timestamp?: string | null;
  succeeded?: boolean;
  authorized?: boolean;
  connectionKey?: string;
};

const ConnectionStatusNotice = ({
  testData,
  connectionOption,
}: {
  testData: ConnectionStatusData;
  connectionOption?: ConnectionSystemTypeMap;
}) => {
  // Show authorization text if required and not authorized
  if (connectionOption?.authorization_required && !testData.authorized) {
    return (
      <Flex align="center" data-testid="connection-status">
        <Text color="error-text.900">Authorization required</Text>
      </Flex>
    );
  }

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
