import { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { DiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredSystemAggregateTable";
import { DiscoveredSystemsTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredSystemsTable";
import { useGetDiscoveryMonitorQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";

const MonitorResultSystems: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const { data: monitorConfig } = useGetDiscoveryMonitorQuery({
    monitor_config_id: monitorId,
  });

  return (
    <FixedLayout title="Action center - Discovered assets by system">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorConfig?.name },
        ]}
      />
      {monitorConfig?.connection_type === "okta" ? (
        <DiscoveredSystemsTable monitorId={monitorId} />
      ) : (
        <DiscoveredSystemAggregateTable monitorId={monitorId} />
      )}
    </FixedLayout>
  );
};

export default MonitorResultSystems;
