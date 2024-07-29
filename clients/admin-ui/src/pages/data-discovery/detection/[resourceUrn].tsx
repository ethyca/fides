import { Heading } from "fidesui";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DETECTION_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DnDBreadcrumbsV2 from "~/features/data-discovery-and-detection/DnDBreadcrumbsV2";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import DetectionResultTable from "~/features/data-discovery-and-detection/tables/DetectionResultTable";

const DataDetectionActivityPage = () => {
  const { resourceUrn, navigateToDetectionResults } = useDiscoveryRoutes();

  return (
    <FixedLayout
      title="Data detection"
      mainProps={{
        padding: "20px 40px 48px",
      }}
    >
      <PageHeader breadcrumbs={false}>
        <Heading>Data detection</Heading>
      </PageHeader>
      {/* <DiscoveryMonitorBreadcrumbs
        parentTitle="Data detection"
        parentLink={DATA_DETECTION_ROUTE}
        resourceUrn={resourceUrn}
        onPathClick={(newResourceUrn) =>
          navigateToDetectionResults({ resourceUrn: newResourceUrn })
        }
      /> */}
      <DnDBreadcrumbsV2
        parentLink={DATA_DETECTION_ROUTE}
        resourceUrn={resourceUrn}
        onPathClick={(newResourceUrn) =>
          navigateToDetectionResults({ resourceUrn: newResourceUrn })
        }
      />
      <DetectionResultTable resourceUrn={resourceUrn} />
    </FixedLayout>
  );
};

export default DataDetectionActivityPage;
