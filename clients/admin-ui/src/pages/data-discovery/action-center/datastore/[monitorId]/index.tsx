import { Result } from "fidesui";
import { NextPage } from "next";
import { useParams } from "next/navigation";

import { useFeatures } from "~/features/common/features";
import {
  ACTION_CENTER_DATASTORE_MONITOR_ACTIVITY_ROUTE,
  ACTION_CENTER_DATASTORE_MONITOR_ROUTE,
} from "~/features/common/nav/routes";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import ActionCenterFields from "~/features/data-discovery-and-detection/action-center/fields/page";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";

export const MONITOR_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]: ACTION_CENTER_DATASTORE_MONITOR_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]: ACTION_CENTER_DATASTORE_MONITOR_ROUTE,
} as const;

export const HELIOS_ACCESS_ERROR =
  "Attempting to access monitor results without the required feature flag enabled";

const DatastoreMonitorResultSystems: NextPage = () => {
  const {
    flags: { heliosV2 },
  } = useFeatures();
  const params = useParams<{ monitorId: string }>();

  const monitorId = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorId;
  const error = !heliosV2 && HELIOS_ACCESS_ERROR;

  if (error) {
    return <Result status="error" title={error} />;
  }

  return (
    <ActionCenterLayout
      monitorId={monitorId}
      routeConfig={MONITOR_ACTION_CENTER_CONFIG}
    >
      {loading ? null : <ActionCenterFields monitorId={monitorId} />}
    </ActionCenterLayout>
  );
};

export default DatastoreMonitorResultSystems;
