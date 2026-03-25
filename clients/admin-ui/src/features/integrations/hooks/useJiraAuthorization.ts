import { useAPIHelper } from "common/hooks";
import { useMessage } from "fidesui";

import { useInitiateJiraOAuthMutation } from "~/features/plus/plus.slice";
import { ConnectionConfigurationResponse, ConnectionType } from "~/types/api";

interface UseJiraAuthorizationProps {
  connection?: ConnectionConfigurationResponse;
  testData: {
    authorized?: boolean;
  };
}

interface UseJiraAuthorizationResult {
  handleAuthorize: () => Promise<void>;
  needsAuthorization: boolean;
  isLoading: boolean;
}

export const useJiraAuthorization = ({
  connection,
  testData,
}: UseJiraAuthorizationProps): UseJiraAuthorizationResult => {
  const [initiateJiraOAuth, { isLoading }] = useInitiateJiraOAuthMutation();
  const { handleError } = useAPIHelper();
  const message = useMessage();

  const handleAuthorize = async () => {
    if (isLoading) {
      return;
    }
    if (!connection?.key) {
      message.error("Authorization failed: connection key not found");
      return;
    }

    try {
      const result = await initiateJiraOAuth({
        connection_key: connection.key,
      }).unwrap();

      window.location.href = result.authorization_url;
    } catch (error) {
      handleError(error);
    }
  };

  const needsAuthorization =
    connection?.connection_type === ConnectionType.JIRA_TICKET &&
    !testData.authorized;

  return {
    handleAuthorize,
    needsAuthorization,
    isLoading,
  };
};
