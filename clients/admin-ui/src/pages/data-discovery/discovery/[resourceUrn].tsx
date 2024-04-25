import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DISCOVERY_ROUTE } from "~/features/common/nav/v2/routes";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DiscoveryMonitorResultTable from "~/features/data-discovery-and-detection/DiscoveryMonitorResultTable";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";

const DataDiscoveryActivityPage = () => {
  const { resourceUrn, navigateToDiscoveryResults } = useDiscoveryRoutes();

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
        resourceUrn={resourceUrn}
        onPathClick={(resourceUrn) =>
          navigateToDiscoveryResults({ resourceUrn })
        }
      />

      {/* TODO: Add filters to get appropiate results */}
      <DiscoveryMonitorResultTable
        resourceUrn={resourceUrn}
        onSelectResource={() => {}}
      />
    </FixedLayout>
  );
};

export default DataDiscoveryActivityPage;
