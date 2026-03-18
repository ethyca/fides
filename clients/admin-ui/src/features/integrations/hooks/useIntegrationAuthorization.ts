import { useMessage } from "fidesui";

import {
  isErrorWithDetail,
  isErrorWithDetailArray,
} from "~/features/common/helpers";
import { useLazyGetAuthorizationUrlQuery } from "~/features/datastore-connections/datastore-connection.slice";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
} from "~/types/api";

interface UseIntegrationAuthorizationProps {
  connection?: ConnectionConfigurationResponse;
  connectionOption?: ConnectionSystemTypeMap;
  testData: {
    authorized?: boolean;
  };
}

interface UseIntegrationAuthorizationResult {
  handleAuthorize: () => Promise<void>;
  needsAuthorization: boolean;
}

export const useIntegrationAuthorization = ({
  connection,
  connectionOption,
  testData,
}: UseIntegrationAuthorizationProps): UseIntegrationAuthorizationResult => {
  const [getAuthorizationUrl] = useLazyGetAuthorizationUrlQuery();
  const message = useMessage();

  const handleAuthorize = async () => {
    if (!connection?.key) {
      message.error("Authorization failed: connection key not found");
      return;
    }

    try {
      const authorizationUrl = (await getAuthorizationUrl(
        connection.key,
      ).unwrap()) as string;

      // Redirect to authorization URL
      window.location.href = authorizationUrl;
    } catch (error: any) {
      let errorMsg = "An unexpected error occurred. Please try again.";
      if (isErrorWithDetail(error)) {
        errorMsg = error.data.detail;
      } else if (isErrorWithDetailArray(error)) {
        errorMsg = error.data.detail[0].msg;
      }
      message.error(errorMsg);
    }
  };

  const needsAuthorization =
    !!connectionOption?.authorization_required && !testData.authorized;

  return {
    handleAuthorize,
    needsAuthorization,
  };
};
