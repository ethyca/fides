import { useFeatures } from "~/features/common/features";

import FrameworkStatus from "./FrameworkStatus";
import SettingsBox from "./SettingsBox";

const GppConfiguration = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  <SettingsBox title="Global Privacy Platform">
    <FrameworkStatus name="GPP" enabled={isTcfEnabled} />
  </SettingsBox>;
};

export default GppConfiguration;
