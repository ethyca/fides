import { Result } from "fidesui";
import { NextPage } from "next";

import { useFeatures } from "~/features/common/features";
import ActionCenterFields from "~/features/data-discovery-and-detection/action-center/fields/page";

const MonitorFeatureError = () => (
  <>
    Attempting to access monitor results without the required feature flag
    enabled
  </>
);

const DatastoreMonitorResultSystems: NextPage = () => {
  const { flags } = useFeatures();

  return flags.heliosV2 ? (
    <ActionCenterFields />
  ) : (
    <Result status="error" title={<MonitorFeatureError />} />
  );
};

export default DatastoreMonitorResultSystems;
