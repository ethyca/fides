import { AntResult as Result } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useDiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/hooks/useDiscoveredSystemAggregateTable";
import { DiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredSystemAggregateTable";

const MonitorFeatureError = () => (
  <>
    Attempting to access monitor results without the required feature flag
    enabled
  </>
);

const MonitorResultSystems: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);

  const { error } = useDiscoveredSystemAggregateTable({
    monitorId,
  });

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your monitor results"
        actions={[
          {
            label: "Return to action center",
            onClick: () => {
              router.push(ACTION_CENTER_ROUTE);
            },
          },
        ]}
      />
    );
  }

  return flags.webMonitor ? (
    <FixedLayout title="Action center - Discovered assets by system">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorId },
        ]}
        isSticky={false}
      />
      <DiscoveredSystemAggregateTable monitorId={monitorId} />
    </FixedLayout>
  ) : (
    <Result status="error" title={<MonitorFeatureError />} />
  );
};

export default MonitorResultSystems;
