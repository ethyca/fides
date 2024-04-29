import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DETECTION_ROUTE } from "~/features/common/nav/v2/routes";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import ActivityTable from "~/features/data-discovery-and-detection/tables/ActivityTable";
import { DiffStatus } from "~/types/api";

const DataDetectionActivityPage = () => {
  const { navigateToDetectionResults } = useDiscoveryRoutes();

  return (
    <FixedLayout
      title="Data detection"
      mainProps={{
        padding: "40px",
        paddingRight: "48px",
      }}
    >
      <DiscoveryMonitorBreadcrumbs
        parentTitle="Data detection"
        parentLink={DATA_DETECTION_ROUTE}
      />
      <ActivityTable
        onRowClick={(row) =>
          navigateToDetectionResults({ resourceUrn: row.urn })
        }
        statusFilters={[DiffStatus.ADDITION, DiffStatus.REMOVAL]}
        childsStatusFilters={[DiffStatus.ADDITION, DiffStatus.REMOVAL]}
      />
    </FixedLayout>
  );
};

export default DataDetectionActivityPage;
