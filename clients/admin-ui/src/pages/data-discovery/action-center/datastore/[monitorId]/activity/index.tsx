import { Result } from "fidesui";
import { NextPage } from "next";
import { useParams } from "next/navigation";

import { useFeatures } from "~/features/common/features";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";

import { HELIOS_ACCESS_ERROR, MONITOR_ACTION_CENTER_CONFIG } from "..";

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
      {loading ? null : <InProgressMonitorTasksList filters={{ monitorId }} />}
    </ActionCenterLayout>
  );
};

export default DatastoreMonitorResultSystems;
