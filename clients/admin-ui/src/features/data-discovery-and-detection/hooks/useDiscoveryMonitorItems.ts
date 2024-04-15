import { useState } from "react";
import {
  useGetAllMonitorsQuery,
  useGetMonitorResultsQuery,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { DiscoveryMonitorItem } from "../types/DiscoveryMonitorItem";

const useDiscoveryMonitorItems = ({ urn }: { urn?: string }) => {
  // const [isLoading, setIsLoading] = useState(false);
  const [discoveryMonitorItems, setDiscoveryMonitorItems] = useState<
    DiscoveryMonitorItem[]
  >([]);

  const { isLoading, data } = useGetMonitorResultsQuery({
    page: 1,
    size: 50,
    monitor_config_id: "test_bq",
    staged_resource_urn: urn,
  });

  return { isLoading, discoveryMonitorItems };
};
export default useDiscoveryMonitorItems;
