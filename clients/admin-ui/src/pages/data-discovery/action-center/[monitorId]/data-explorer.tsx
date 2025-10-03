import { AntResult as Result, AntText as Text } from "fidesui";
import { NextPage } from "next";

import { useFeatures } from "~/features/common/features";
import ActionCenterFields from "~/features/data-discovery-and-detection/action-center/fields/page";

const AlphaMonitorError = () => (
  <>
    Attempting to access the alpha version of monitor results without setting
    the <Text code>alphaFullActionCenter</Text> flag
  </>
);

const AlphaMonitorResultSystems: NextPage = () => {
  const { flags } = useFeatures();

  return flags.alphaFullActionCenter ? (
    <ActionCenterFields />
  ) : (
    <Result status="error" title={<AlphaMonitorError />} />
  );
};

export default AlphaMonitorResultSystems;
