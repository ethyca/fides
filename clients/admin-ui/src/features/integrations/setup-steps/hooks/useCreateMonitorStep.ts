import { useGetMonitorsByIntegrationQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";

import { BaseStepHookParams, Step } from "./types";

export const useCreateMonitorStep = (params: BaseStepHookParams): Step => {
  // Use the monitors query to check if any monitors exist for this integration
  const { data: monitorsData } = useGetMonitorsByIntegrationQuery(
    {
      connection_config_key: params.testData?.connectionKey,
      page: 1,
      size: 1,
    },
    // Only run the query if we have a connection key
    { skip: !params.testData?.connectionKey },
  );

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
