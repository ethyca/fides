import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { formatDate } from "~/features/common/utils";
import { useLazyGetDatastoreConnectionStatusQuery } from "~/features/datastore-connections/datastore-connection.slice";
import { ConnectionStatusData } from "~/features/integrations/ConnectionStatusNotice";
import { ConnectionConfigurationResponse } from "~/types/api";

const useTestConnection = (
  integration: ConnectionConfigurationResponse | undefined,
) => {
  const [
    connectionTestTrigger,
    { data, fulfilledTimeStamp, isLoading: queryIsLoading, isFetching },
  ] = useLazyGetDatastoreConnectionStatusQuery();

  const toast = useToast();

  const testConnection = async () => {
    if (!integration) {
      return;
    }
    const result = await connectionTestTrigger(integration.key);
    if (result.isError) {
      toast({
        status: "error",
        description: getErrorMessage(
          result.error,
          "Unable to test connection. Please try again.",
        ),
      });
    } else if (result.data?.test_status === "succeeded") {
      toast({ status: "success", description: "Connected successfully" });
    } else if (result.data?.test_status === "failed") {
      toast({ status: "warning", description: "Connection test failed" });
    }
  };

  const testData: ConnectionStatusData = {
    timestamp: fulfilledTimeStamp
      ? formatDate(fulfilledTimeStamp)
      : integration?.last_test_timestamp,
    succeeded: data
      ? data.test_status === "succeeded"
      : Boolean(integration?.last_test_succeeded),
  };

  const isLoading = queryIsLoading || isFetching;

  return {
    testConnection,
    isLoading,
    testData,
  };
};

export default useTestConnection;
