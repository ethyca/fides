import { useRouter } from "next/router";

import {
  DATA_DETECTION_ROUTE_DETAIL,
  DATA_DISCOVERY_ROUTE_DETAIL,
} from "~/features/common/nav/routes";

const useDiscoveryRoutes = () => {
  const router = useRouter();
  const monitorId = router.query.monitorId as string;
  const currentResourceUrn = router.query.resourceUrn as string;

  const navigateToDetectionResults = ({
    resourceUrn,
    filterTabIndex,
  }: {
    resourceUrn: string;
    filterTabIndex?: number;
  }) => {
    router.push({
      pathname: DATA_DETECTION_ROUTE_DETAIL,
      query: {
        resourceUrn,
        filterTabIndex,
      },
    });
  };

  const navigateToDiscoveryResults = ({
    resourceUrn,
    filterTabIndex,
  }: {
    resourceUrn: string;
    filterTabIndex?: number;
  }) => {
    router.push({
      pathname: DATA_DISCOVERY_ROUTE_DETAIL,
      query: {
        resourceUrn,
        filterTabIndex,
      },
    });
  };

  return {
    monitorId,
    resourceUrn: currentResourceUrn,
    navigateToDetectionResults,
    navigateToDiscoveryResults,
  };
};
export default useDiscoveryRoutes;
