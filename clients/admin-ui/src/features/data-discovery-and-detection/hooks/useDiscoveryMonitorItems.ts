import { useState } from "react";
import { DiscoveryMonitorItem } from "../types/DiscoveryMonitorItem";

const useDiscoveryMonitorItems = ({ urn }: { urn: string }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [discoveryMonitorItems, setDiscoveryMonitorItems] = useState<
    DiscoveryMonitorItem[]
  >([]);

  return { isLoading, discoveryMonitorItems };
};
export default useDiscoveryMonitorItems;
