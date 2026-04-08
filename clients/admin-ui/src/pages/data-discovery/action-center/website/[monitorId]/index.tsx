import { Result } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import { useDiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/hooks/useDiscoveredSystemAggregateTable";
import MonitorStats from "~/features/data-discovery-and-detection/action-center/MonitorStats";
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
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Action center"
          breadcrumbItems={[
            { title: "All activity", href: ACTION_CENTER_ROUTE },
            { title: monitorId },
          ]}
        />
      </SidePanel>
      <FixedLayout title="Action center - Discovered assets by system">
        <MonitorStats monitorId={monitorId} />
        <DiscoveredSystemAggregateTable monitorId={monitorId} />
      </FixedLayout>
    </>
  ) : (
    <Result status="error" title={<MonitorFeatureError />} />
  );
};

export default MonitorResultSystems;
