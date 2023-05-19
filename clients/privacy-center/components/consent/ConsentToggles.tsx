import { useSettings } from "~/features/common/settings.slice";
import ConfigDrivenConsent from "./ConfigDrivenConsent";
import NoticeDrivenConsent from "./NoticeDrivenConsent";

const ConsentToggles = () => {
  const settings = useSettings();
  const { IS_OVERLAY_DISABLED } = settings;

  if (IS_OVERLAY_DISABLED) {
    return <ConfigDrivenConsent />;
  }
  return <NoticeDrivenConsent />;
};

export default ConsentToggles;
