import { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFeatures } from "~/features/common/features";
import {
  ACTION_CENTER_ACTIVITY_ROUTE,
  ACTION_CENTER_ROUTE,
} from "~/features/common/nav/routes";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { useGetAggregateMonitorResultsQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import MonitorList from "~/features/data-discovery-and-detection/action-center/MonitorList";
import { MONITOR_TYPES } from "~/features/data-discovery-and-detection/action-center/utils/getMonitorType";

export const ROOT_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]: ACTION_CENTER_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]: ACTION_CENTER_ROUTE,
};

const ActionCenterPage: NextPage = () => {
  const { flags } = useFeatures();
  const { webMonitor: webMonitorEnabled, heliosV2: heliosV2Enabled } = flags;

  // Build monitor_type filter based on enabled feature flags
  const monitorTypes: MONITOR_TYPES[] = [
    ...(webMonitorEnabled ? [MONITOR_TYPES.WEBSITE] : []),
    ...(heliosV2Enabled ? [MONITOR_TYPES.DATASTORE] : []),
  ];

  const { error } = useGetAggregateMonitorResultsQuery({
    page: 1,
    size: 20,
    monitor_type: monitorTypes.length > 0 ? monitorTypes : undefined,
  });

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your monitor results"
      />
    );
  }

  return (
    <ActionCenterLayout routeConfig={ROOT_ACTION_CENTER_CONFIG}>
      <MonitorList />
    </ActionCenterLayout>
  );
};

export default ActionCenterPage;
