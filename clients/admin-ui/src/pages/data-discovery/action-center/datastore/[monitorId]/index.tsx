import { AntResult as Result } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";
import ActionCenterFields from "~/features/data-discovery-and-detection/action-center/fields/page";
import { ActionCenterHash } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterHashNavigation";

const MonitorFeatureError = () => (
  <>
    Attempting to access monitor results without the required feature flag
    enabled
  </>
);

const DatastoreMonitorResultSystems: NextPage = () => {
  const {
    flags: { heliosV2 },
  } = useFeatures();
  const {
    query: { monitorId },
  } = useRouter();

  if (!heliosV2) {
    return <Result status="error" title={<MonitorFeatureError />} />;
  }

  return typeof monitorId === "string" ? (
    <ActionCenterLayout
      monitor={monitorId}
      hashRoutes={{
        [ActionCenterHash.ATTENTION_REQUIRED]: (
          <ActionCenterFields monitorId={decodeURIComponent(monitorId)} />
        ),
        [ActionCenterHash.ACTIVITY]: (
          <InProgressMonitorTasksList filters={{ monitorId }} />
        ),
      }}
    />
  ) : (
    <Result status="error" title="Cannot find monitor" />
  );
};

export default DatastoreMonitorResultSystems;
