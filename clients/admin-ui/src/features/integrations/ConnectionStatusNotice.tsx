import { ChakraFlex as Flex, ChakraText as Text, Icons, Spin } from "fidesui";

import { formatDate } from "~/features/common/utils";
import { ConnectionSystemTypeMap, ConnectionType } from "~/types/api";

export type ConnectionStatusData = {
  timestamp?: string | null;
  succeeded?: boolean;
  authorized?: boolean;
  connectionKey?: string;
  failureReason?: string;
};

const ConnectionStatusNotice = ({
  testData,
  connectionOption,
  connectionType,
  isTestingConnection,
}: {
  testData: ConnectionStatusData;
  connectionOption?: ConnectionSystemTypeMap;
  connectionType?: ConnectionType;
  isTestingConnection?: boolean;
}) => {
  const isJiraTicket = connectionType === ConnectionType.JIRA_TICKET;
  const requiresAuth =
    (connectionOption?.authorization_required || isJiraTicket) &&
    !testData.authorized;

  if (isTestingConnection) {
    return (
      <Flex align="center" gap={8} data-testid="connection-status">
        <Spin size="small" />
        <Text>Testing connection…</Text>
      </Flex>
    );
  }

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
      <Icons.CheckmarkFilled size={16} className="mr-2" />
      <Text>Last connected {testDate}</Text>
    </Flex>
  ) : (
    <Flex color="error-text.900" align="center" data-testid="connection-status">
      <Icons.WarningAltFilled size={16} className="mr-2" />
      <Text>
        Last connection failed {testDate}
        {isJiraTicket && testData.authorized
          ? " — Jira authorization may have expired"
          : ""}
      </Text>
    </Flex>
  );
};

export default ConnectionStatusNotice;
