import { Button, Flex, Icons, Result } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";
import { useDispatch } from "react-redux";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import {
  ACTION_CENTER_ACTIVITY_ROUTE,
  ACTION_CENTER_ROUTE,
  ACTION_CENTER_WEBSITE_MONITOR_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  actionCenterUtil,
  useCalcAggregateStatisticsMutation,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { monitorFieldUtil } from "~/features/data-discovery-and-detection/action-center/fields/monitor-fields.slice";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import { useDiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/hooks/useDiscoveredSystemAggregateTable";
import MonitorStats from "~/features/data-discovery-and-detection/action-center/MonitorStats";
import { DiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredSystemAggregateTable";
import WebsiteMonitorResults from "~/features/data-discovery-and-detection/action-center/website/WebsiteMonitorResults";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

const MonitorFeatureError = () => (
  <>
    Attempting to access monitor results without the required feature flag
    enabled
  </>
);

const WEBSITE_MONITOR_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]: ACTION_CENTER_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]: ACTION_CENTER_WEBSITE_MONITOR_ROUTE,
} as const;

/**
 * New single-page tree + list + detail-drawer view, consistent with the
 * datastore/infrastructure monitors. Gated behind the `webMonitorExplorer`
 * flag so it can coexist with the legacy two-page table flow below.
 */
const WebsiteMonitorExplorerPage = ({ monitorId }: { monitorId: string }) => {
  const dispatch = useDispatch();
  const [trigger] = useCalcAggregateStatisticsMutation();
  const [pageSettings, setPageSettings] = useState({
    showApproved: false,
    showIgnored: false,
  });

  return (
    <ActionCenterLayout
      monitorId={monitorId}
      monitorType={APIMonitorType.WEBSITE}
      routeConfig={WEBSITE_MONITOR_ACTION_CENTER_CONFIG}
      pageSettings={{
        badgeProps: {
          count: Object.values(pageSettings).filter(Boolean).length,
          size: "small",
        },
        dropdownProps: {
          trigger: ["click"],
          menu: {
            selectable: true,
            selectedKeys: Object.entries(pageSettings).flatMap(
              ([key, value]) => (value ? [key] : []),
            ),
            onSelect: (info) =>
              setPageSettings({
                showApproved: info.selectedKeys.includes("showApproved"),
                showIgnored: info.selectedKeys.includes("showIgnored"),
              }),
            onDeselect: (info) =>
              setPageSettings({
                showApproved: info.selectedKeys.includes("showApproved"),
                showIgnored: info.selectedKeys.includes("showIgnored"),
              }),
            items: [
              { key: "showApproved", label: "Show approved" },
              { key: "showIgnored", label: "Show ignored" },
            ],
          },
        },
      }}
      refresh={async () => {
        dispatch(
          actionCenterUtil.invalidateTags(["Discovery Monitor Results"]),
        );
        await trigger({
          monitor_config_id: monitorId,
          monitor_type: APIMonitorType.WEBSITE,
        });
      }}
    >
      {monitorId ? (
        <WebsiteMonitorResults
          monitorId={monitorId}
          showApproved={pageSettings.showApproved}
          showIgnored={pageSettings.showIgnored}
        />
      ) : null}
    </ActionCenterLayout>
  );
};

/**
 * Legacy two-page table flow (systems table -> per-system assets table),
 * gated behind the original `webMonitor` flag.
 */
const WebsiteMonitorSystemsTablePage = ({
  monitorId,
}: {
  monitorId: string;
}) => {
  const router = useRouter();
  const dispatch = useDispatch();
  const [refreshing, setRefreshing] = useState(false);
  const [trigger] = useCalcAggregateStatisticsMutation();

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

  return (
    <FixedLayout title="Action center - Discovered assets by system">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorId },
        ]}
        isSticky={false}
        rightContent={
          <Flex gap="small">
            <Button
              aria-label="Page refresh"
              icon={<Icons.Renew />}
              onClick={async () => {
                setRefreshing(true);
                dispatch(
                  monitorFieldUtil.invalidateTags(["Monitor Field Results"]),
                );
                try {
                  await trigger({
                    monitor_config_id: monitorId,
                    monitor_type: APIMonitorType.WEBSITE,
                  });
                } finally {
                  setRefreshing(false);
                }
              }}
              disabled={refreshing}
              loading={refreshing}
            />
          </Flex>
        }
      />
      <MonitorStats
        monitorId={monitorId}
        monitorType={APIMonitorType.WEBSITE}
      />
      <DiscoveredSystemAggregateTable monitorId={monitorId} />
    </FixedLayout>
  );
};

const MonitorResultSystems: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);

  if (flags.webMonitorExplorer) {
    return <WebsiteMonitorExplorerPage monitorId={monitorId} />;
  }

  if (flags.webMonitor) {
    return <WebsiteMonitorSystemsTablePage monitorId={monitorId} />;
  }

  return <Result status="error" title={<MonitorFeatureError />} />;
};

export default MonitorResultSystems;
