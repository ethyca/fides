import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DISCOVERY_ROUTE } from "~/features/common/nav/v2/routes";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import ActivityTable from "~/features/data-discovery-and-detection/tables/ActivityTable";
import { DiffStatus } from "~/types/api";

const DataDiscoveryActivityPage = () => {
  const { navigateToDiscoveryResults } = useDiscoveryRoutes();

  return (
    <FixedLayout
      title="Data discovery"
      mainProps={{
        padding: "40px",
        paddingRight: "48px",
      }}
    >
      <DiscoveryMonitorBreadcrumbs
        parentTitle="Data discovery"
        parentLink={DATA_DISCOVERY_ROUTE}
      />

      <ActivityTable
        onRowClick={(row) =>
          navigateToDiscoveryResults({ resourceUrn: row.urn })
        }
        statusFilters={[
          DiffStatus.CLASSIFICATION_ADDITION,
          DiffStatus.CLASSIFICATION_UPDATE,
        ]}
      />
    </FixedLayout>
  );
};

export default DataDiscoveryActivityPage;
