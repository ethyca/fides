import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DETECTION_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import DetectionResultTable from "~/features/data-discovery-and-detection/tables/DetectionResultTable";

const DataDetectionActivityPage = () => {
  const { resourceUrn, navigateToDetectionResults } = useDiscoveryRoutes();

  return (
    <FixedLayout title="Data detection">
      <PageHeader heading="Data detection">
        <DiscoveryMonitorBreadcrumbs
          parentLink={DATA_DETECTION_ROUTE}
          resourceUrn={resourceUrn}
          onPathClick={(newResourceUrn) =>
            navigateToDetectionResults({ resourceUrn: newResourceUrn })
          }
        />
      </PageHeader>

      <DetectionResultTable resourceUrn={resourceUrn} />
    </FixedLayout>
  );
};

export default DataDetectionActivityPage;
