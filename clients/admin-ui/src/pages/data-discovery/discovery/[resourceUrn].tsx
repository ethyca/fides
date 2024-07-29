import { Heading } from "fidesui";
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
    <FixedLayout
      title="Data discovery"
      mainProps={{
        padding: "20px 40px 48px",
      }}
    >
      <PageHeader breadcrumbs={false}>
        <Heading>Data discovery</Heading>
      </PageHeader>
      <DiscoveryMonitorBreadcrumbs
        parentTitle="Data discovery"
        parentLink={DATA_DISCOVERY_ROUTE}
        resourceUrn={resourceUrn}
        onPathClick={(newResourceUrn) =>
          navigateToDiscoveryResults({ resourceUrn: newResourceUrn })
        }
      />
      <DiscoveryResultTable resourceUrn={resourceUrn} />
    </FixedLayout>
  );
};

export default DataDiscoveryActivityPage;
