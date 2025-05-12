import { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { DiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredSystemAggregateTable";

const MonitorResultSystems: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);

  return (
    <FixedLayout title="Action center - Discovered assets by system">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorId },
        ]}
      />
      <DiscoveredSystemAggregateTable monitorId={monitorId} />
    </FixedLayout>
  );
};

export default MonitorResultSystems;
