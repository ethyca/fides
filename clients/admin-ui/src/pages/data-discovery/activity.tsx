import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import ActivityTable from "~/features/data-discovery-and-detection/tables/ActivityTable";
import { ResourceActivityTypeEnum } from "~/features/data-discovery-and-detection/types/ResourceActivityTypeEnum";
import findActivityType from "~/features/data-discovery-and-detection/utils/getResourceActivityLabel";
import { DiffStatus, StagedResource } from "~/types/api";

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
    <FixedLayout title="Data discovery">
      <PageHeader heading="All activity" />
      <ActivityTable
        onRowClick={navigateToResourceResults}
        statusFilters={[
          DiffStatus.ADDITION,
          DiffStatus.REMOVAL,
          DiffStatus.CLASSIFICATION_ADDITION,
          DiffStatus.CLASSIFICATION_UPDATE,
        ]}
        childsStatusFilters={[
          DiffStatus.ADDITION,
          DiffStatus.REMOVAL,
          DiffStatus.CLASSIFICATION_ADDITION,
          DiffStatus.CLASSIFICATION_UPDATE,
        ]}
      />
    </FixedLayout>
  );
};

export default DataDiscoveryAndDetectionActivityPage;
