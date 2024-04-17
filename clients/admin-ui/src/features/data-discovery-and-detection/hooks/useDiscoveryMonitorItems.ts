import { useState } from "react";

import {
  useGetAllMonitorsQuery,
  useGetMonitorResultsQuery,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";

import { DiscoveryMonitorItem } from "../types/DiscoveryMonitorItem";

const useDiscoveryMonitorItems = ({ urn }: { urn?: string }) => {};
export default useDiscoveryMonitorItems;
