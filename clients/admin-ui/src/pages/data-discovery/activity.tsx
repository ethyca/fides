import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DETECTION_DISCOVERY_ACTIVITY_ROUTE } from "~/features/common/nav/v2/routes";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import ActivityTable from "~/features/data-discovery-and-detection/tables/ActivityTable";
import { ResourceActivityTypeEnum } from "~/features/data-discovery-and-detection/types/ResourceActivityTypeEnum";
import findActivityType from "~/features/data-discovery-and-detection/utils/findResourceActivityType";
import { StagedResource } from "~/types/api";

const DataDiscoveryAndDetectionActivityPage = () => {
  const { navigateToDetectionResults, navigateToDiscoveryResults } =
    useDiscoveryRoutes();

  const navigateToResourceResults = (resource: StagedResource) => {
    const activityType = findActivityType(resource);

    if (activityType === ResourceActivityTypeEnum.DATASET) {
      navigateToDetectionResults({ resourceUrn: resource.urn });
      return;
    }

    navigateToDiscoveryResults({ resourceUrn: resource.urn });
  };

  return (
    <FixedLayout
      title="Data discovery"
      mainProps={{
        padding: "40px",
        paddingRight: "48px",
      }}
    >
      <DiscoveryMonitorBreadcrumbs
        parentTitle="Detection & discovery"
        parentLink={DETECTION_DISCOVERY_ACTIVITY_ROUTE}
      />
      <ActivityTable onRowClick={navigateToResourceResults} />
    </FixedLayout>
  );
};

export default DataDiscoveryAndDetectionActivityPage;
