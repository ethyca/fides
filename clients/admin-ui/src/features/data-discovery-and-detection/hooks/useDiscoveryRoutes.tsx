import { useRouter } from "next/router";

import {
  DATA_DISCOVERY_MONITOR_DETAIL_ROUTE,
  DATA_DISCOVERY_RESOURCE_DETAIL_ROUTE,
} from "~/features/common/nav/v2/routes";

const useDiscoveryRoutes = () => {
  const router = useRouter();
  const monitorId = router.query.monitorId as string;
  const resourceUrn = router.query.resourceUrn as string;

  const navigateToMonitorDetails = ({ monitorId }: { monitorId: string }) => {
    router.push({
      pathname: DATA_DISCOVERY_MONITOR_DETAIL_ROUTE,
      query: {
        monitorId,
      },
    });
  };

  const navigateToResourceDetails = ({
    monitorId,
    resourceUrn,
  }: {
    monitorId: string;
    resourceUrn: string;
  }) => {
    router.push({
      pathname: DATA_DISCOVERY_RESOURCE_DETAIL_ROUTE,
      query: {
        monitorId,
        resourceUrn,
      },
    });
  };

  return {
    monitorId,
    resourceUrn,
    navigateToMonitorDetails,
    navigateToResourceDetails,
  };
};
export default useDiscoveryRoutes;
