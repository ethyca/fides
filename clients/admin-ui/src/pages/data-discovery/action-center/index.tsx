import { NextPage } from "next";
import { useDispatch } from "react-redux";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFeatures } from "~/features/common/features";
import {
  ACTION_CENTER_ACTIVITY_ROUTE,
  ACTION_CENTER_ROUTE,
} from "~/features/common/nav/routes";
import {
  useCalcAggregateStatisticsMutation,
  useGetAggregateMonitorResultsQuery,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { monitorFieldUtil } from "~/features/data-discovery-and-detection/action-center/fields/monitor-fields.slice";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import MonitorList from "~/features/data-discovery-and-detection/action-center/MonitorList";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

export const ROOT_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]: ACTION_CENTER_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]: ACTION_CENTER_ROUTE,
};

const ActionCenterPage: NextPage = () => {
  const dispatch = useDispatch();
  const { flags } = useFeatures();
  const { webMonitor: webMonitorEnabled } = flags;

  const [trigger] = useCalcAggregateStatisticsMutation();

  // Build monitor_type filter based on enabled feature flags.
  // BE doesn't yet accept CLOUD_INFRASTRUCTURE (returns 422); the AWS row is
  // injected client-side by MonitorList, so we omit it from the BE request.
  const monitorTypes: APIMonitorType[] = [
    ...(webMonitorEnabled ? [APIMonitorType.WEBSITE] : []),
    APIMonitorType.DATASTORE,
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
    <ActionCenterLayout
      routeConfig={ROOT_ACTION_CENTER_CONFIG}
      refresh={async () => {
        dispatch(
          monitorFieldUtil.invalidateTags(["Discovery Monitor Results"]),
        );
        // Skip cloud_infrastructure refresh — BE doesn't accept it yet.
        await Promise.all([
          trigger({ monitor_type: APIMonitorType.INFRASTRUCTURE }),
          trigger({ monitor_type: APIMonitorType.DATASTORE }),
          trigger({ monitor_type: APIMonitorType.WEBSITE }),
        ]);
      }}
    >
      <MonitorList />
    </ActionCenterLayout>
  );
};

export default ActionCenterPage;
