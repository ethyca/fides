import { NextPage } from "next";
import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useDiscoveredInfrastructureSystemsTable } from "~/features/data-discovery-and-detection/action-center/hooks/useDiscoveredInfrastructureSystemsTable";
import { DiscoveredInfrastructureSystemsTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredInfrastructureSystemsTable";

const MonitorResultSystems: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);

  const { error } = useDiscoveredInfrastructureSystemsTable({
    monitorId,
  });

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your systems"
      />
    );
  }

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
