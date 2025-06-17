import { useGetMonitorsByIntegrationQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import getIntegrationTypeInfo from "~/features/integrations/add-integration/allIntegrationTypes";
import { IntegrationFeatureEnum } from "~/features/integrations/IntegrationFeatureEnum";

import { BaseStepHookParams, Step } from "./types";

export const useCreateMonitorStep = (
  params: BaseStepHookParams,
): Step | null => {
  // Get the integration type info to check enabled features
  const { enabledFeatures } = getIntegrationTypeInfo(
    params.connection.connection_type,
    params.connection.saas_config?.type,
  );

  const hasDataDiscoverySupport = enabledFeatures?.includes(
    IntegrationFeatureEnum.DATA_DISCOVERY,
  );

  // Use the monitors query to check if any monitors exist for this integration
  const { data: monitorsData } = useGetMonitorsByIntegrationQuery(
    {
      connection_config_key: params.testData?.connectionKey,
      page: 1,
      size: 1,
    },
    // Only run the query if we have a connection key and data discovery is enabled
    {
      skip: !params.testData?.connectionKey || !hasDataDiscoverySupport,
    },
  );

  // If the integration doesn't have data discovery enabled, don't show the monitor step
  if (!hasDataDiscoverySupport) {
    return null;
  }

  // Check if we have any monitors for this integration
  const hasMonitors = !!monitorsData?.items?.length;

  return {
    title: "Create monitor",
    description: hasMonitors
      ? "Data monitor created successfully"
      : "Use the Data discovery tab in this page to add a new monitor",
    state: hasMonitors ? "finish" : "process",
  };
};
