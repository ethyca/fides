import { formatDate } from "~/features/common/utils";
import { useLazyGetDatastoreConnectionStatusQuery } from "~/features/datastore-connections/datastore-connection.slice";
import { ConnectionStatusData } from "~/features/integrations/ConnectionStatusNotice";
import { ConnectionConfigurationResponse } from "~/types/api";

const useTestConnection = (
  integration: ConnectionConfigurationResponse | undefined
) => {
  const [
    connectionTestTrigger,
    { data, fulfilledTimeStamp, isLoading: queryIsLoading, isFetching },
  ] = useLazyGetDatastoreConnectionStatusQuery();

  const testConnection = () => {
    if (!integration) {
      return;
    }
    connectionTestTrigger(integration.key);
  };

  const testData: ConnectionStatusData = {
    timestamp: fulfilledTimeStamp
      ? formatDate(fulfilledTimeStamp)
      : integration?.last_test_timestamp,
    succeeded:
      data?.test_status === "succeeded" || integration?.last_test_succeeded,
  };

  const isLoading = queryIsLoading || isFetching;

  return {
    testConnection,
    isLoading,
    testData,
  };
};

export default useTestConnection;
