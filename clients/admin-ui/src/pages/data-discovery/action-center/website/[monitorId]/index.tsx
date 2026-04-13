import { Button, Flex, Icons, Result } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";
import { useDispatch } from "react-redux";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useCalcAggregateStatisticsMutation } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { monitorFieldUtil } from "~/features/data-discovery-and-detection/action-center/fields/monitor-fields.slice";
import { useDiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/hooks/useDiscoveredSystemAggregateTable";
import MonitorStats from "~/features/data-discovery-and-detection/action-center/MonitorStats";
import { DiscoveredSystemAggregateTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredSystemAggregateTable";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

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

  return flags.webMonitor ? (
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
  ) : (
    <Result status="error" title={<MonitorFeatureError />} />
  );
};

export default MonitorResultSystems;
