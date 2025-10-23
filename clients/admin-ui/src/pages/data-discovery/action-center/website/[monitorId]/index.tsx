import { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { DiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredSystemAggregateTable";

const MonitorResultSystems: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);

  return (
    <Layout title="Action center - Discovered assets by system">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorId },
        ]}
        isSticky={false}
      />
      <DiscoveredSystemAggregateTable monitorId={monitorId} />
    </Layout>
  );
};

export default MonitorResultSystems;
