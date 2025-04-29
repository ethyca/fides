import { useAPIHelper } from "common/hooks";
import {
  AntButton as Button,
  CheckCircleIcon,
  Flex,
  Text,
  WarningTwoIcon,
} from "fidesui";

import { formatDate } from "~/features/common/utils";
import { useLazyGetAuthorizationUrlQuery } from "~/features/datastore-connections/datastore-connection.slice";
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
  onAuthorize,
  isAuthorizing = false,
}: {
  testData: ConnectionStatusData;
  connectionOption?: ConnectionSystemTypeMap;
  onAuthorize?: () => void;
  isAuthorizing?: boolean;
}) => {
  const [getAuthorizationUrl] = useLazyGetAuthorizationUrlQuery();
  const { handleError } = useAPIHelper();

  const handleAuthorize = async () => {
    if (!testData.connectionKey) {
      return;
    }

    try {
      const authorizationUrl = (await getAuthorizationUrl(
        testData.connectionKey,
      ).unwrap()) as string;

      // Redirect to authorization URL
      window.location.href = authorizationUrl;
    } catch (error) {
      handleError(error);
    }
  };

  // Show authorization button if required and not authorized
  if (connectionOption?.authorization_required && !testData.authorized) {
    return (
      <Flex align="center" data-testid="connection-status">
        <Text color="error-text.900" mr={4}>
          Authorization required
        </Text>
        <Button
          loading={isAuthorizing}
          onClick={onAuthorize || handleAuthorize}
        >
          Authorize integration
        </Button>
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
