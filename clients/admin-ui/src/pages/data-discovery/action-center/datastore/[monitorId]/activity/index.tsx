import { NextPage } from "next";
import { useParams } from "next/navigation";

import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";

import { MONITOR_ACTION_CENTER_CONFIG } from "..";

const DatastoreMonitorResultSystems: NextPage = () => {
  const params = useParams<{ monitorId: string }>();

  const monitorKey = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorKey;

  return (
    <ActionCenterLayout
      monitorId={monitorKey}
      routeConfig={MONITOR_ACTION_CENTER_CONFIG}
    >
      {loading ? null : <InProgressMonitorTasksList filters={{ monitorKey }} />}
    </ActionCenterLayout>
  );
};

export default DatastoreMonitorResultSystems;
