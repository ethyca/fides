import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DISCOVERY_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import DiscoveryResultTable from "~/features/data-discovery-and-detection/tables/DiscoveryResultTable";

const DataDiscoveryActivityPage = () => {
  const { resourceUrn, navigateToDiscoveryResults } = useDiscoveryRoutes();

  return (
    <FixedLayout title="Data discovery">
      <PageHeader heading="Data discovery">
        <DiscoveryMonitorBreadcrumbs
          parentLink={DATA_DISCOVERY_ROUTE}
          resourceUrn={resourceUrn}
          onPathClick={(newResourceUrn) =>
            navigateToDiscoveryResults({ resourceUrn: newResourceUrn })
          }
        />
      </PageHeader>

      <DiscoveryResultTable resourceUrn={resourceUrn} />
    </FixedLayout>
  );
};

export default DataDiscoveryActivityPage;
