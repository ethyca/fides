import { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { DiscoveredInfrastructureSystemsTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredInfrastructureSystemsTable";

const MonitorResultSystems: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);

  return (
    <FixedLayout title="Action center - Discovered infrastructure systems">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorId },
        ]}
      />
      <DiscoveredInfrastructureSystemsTable monitorId={monitorId} />
    </FixedLayout>
  );
};

export default MonitorResultSystems;
