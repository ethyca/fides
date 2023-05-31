import { useSettings } from "~/features/common/settings.slice";
import { ConsentPreferences } from "~/types/api";

import ConfigDrivenConsent from "./ConfigDrivenConsent";
import NoticeDrivenConsent from "./NoticeDrivenConsent";

const ConsentToggles = ({
  storePreferences,
}: {
  storePreferences: (data: ConsentPreferences) => void;
}) => {
  const settings = useSettings();
  const { IS_OVERLAY_DISABLED } = settings;

  if (IS_OVERLAY_DISABLED) {
    return <ConfigDrivenConsent storePreferences={storePreferences} />;
  }
  return <NoticeDrivenConsent />;
};

export default ConsentToggles;
