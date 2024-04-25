import { useRouter } from "next/router";

import {
  DATA_DETECTION_ROUTE_DETAIL,
  DATA_DISCOVERY_ROUTE_DETAIL,
} from "~/features/common/nav/v2/routes";
import { DiffStatus, StagedResource } from "~/types/api";

const useDiscoveryRoutes = () => {
  const router = useRouter();
  const monitorId = router.query.monitorId as string;
  const resourceUrn = router.query.resourceUrn as string;

  const navigateToDetectionResults = ({
    resourceUrn,
  }: {
    resourceUrn: string;
  }) => {
    router.push({
      pathname: DATA_DETECTION_ROUTE_DETAIL,
      query: {
        resourceUrn,
      },
    });
  };

  const navigateToDiscoveryResults = ({
    resourceUrn,
  }: {
    resourceUrn: string;
  }) => {
    router.push({
      pathname: DATA_DISCOVERY_ROUTE_DETAIL,
      query: {
        resourceUrn,
      },
    });
  };

  const navigateToResourceResults = (resource: StagedResource) => {
    if (
      resource.diff_status === DiffStatus.ADDITION ||
      resource.diff_status === DiffStatus.REMOVAL
    ) {
      navigateToDetectionResults({ resourceUrn: resource.urn });
      return;
    }
    navigateToDiscoveryResults({ resourceUrn: resource.urn });
  };

  return {
    monitorId,
    resourceUrn,
    navigateToDetectionResults,
    navigateToDiscoveryResults,
    navigateToResourceResults,
  };
};
export default useDiscoveryRoutes;
