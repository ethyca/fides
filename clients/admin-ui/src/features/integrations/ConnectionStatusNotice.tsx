import {
  ChakraCheckCircleIcon as CheckCircleIcon,
  ChakraFlex as Flex,
  ChakraText as Text,
  ChakraWarningTwoIcon as WarningTwoIcon,
} from "fidesui";

import { formatDate } from "~/features/common/utils";
import { ConnectionSystemTypeMap, ConnectionType } from "~/types/api";

export type ConnectionStatusData = {
  timestamp?: string | null;
  succeeded?: boolean;
  authorized?: boolean;
  connectionKey?: string;
};

const ConnectionStatusNotice = ({
  testData,
  connectionOption,
  connectionType,
}: {
  testData: ConnectionStatusData;
  connectionOption?: ConnectionSystemTypeMap;
  connectionType?: ConnectionType;
}) => {
  const isJiraTicket = connectionType === ConnectionType.JIRA_TICKET;
  const requiresAuth =
    (connectionOption?.authorization_required || isJiraTicket) &&
    !testData.authorized;

  if (requiresAuth) {
    return (
      <Flex align="center" data-testid="connection-status">
        <Text color="error-text.900">
          {isJiraTicket
            ? "Connection not authorized"
            : "Authorization required"}
        </Text>
      </Flex>
    );
  }

  if (!testData.timestamp) {
    return (
      <Flex align="center">
        <Text data-testid="connection-status">Connection not tested</Text>
      </Flex>
    );
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
