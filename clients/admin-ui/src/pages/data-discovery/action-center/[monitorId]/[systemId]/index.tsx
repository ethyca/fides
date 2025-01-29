import { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { DiscoveredAssetsTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredAssetsTable";

const MonitorResultAssets: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const systemId = decodeURIComponent(router.query.systemId as string);
  const [systemName, setSystemName] = useState(
    systemId === UNCATEGORIZED_SEGMENT ? "Uncategorized assets" : systemId,
  );

  return (
    <FixedLayout title="Action center - Discovered assets">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorId, href: `${ACTION_CENTER_ROUTE}/${monitorId}` },
          {
            title:
              systemId === UNCATEGORIZED_SEGMENT
                ? "Uncategorized assets"
                : systemName,
          },
        ]}
      />
      <DiscoveredAssetsTable
        monitorId={monitorId}
        systemId={systemId}
        onSystemName={setSystemName}
      />
    </FixedLayout>
  );
};

export default MonitorResultAssets;
