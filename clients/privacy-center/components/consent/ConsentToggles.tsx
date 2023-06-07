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
  const { IS_OVERLAY_ENABLED } = settings;

  if (IS_OVERLAY_ENABLED) {
    return <NoticeDrivenConsent />;
  }
  return <ConfigDrivenConsent storePreferences={storePreferences} />;
};

export default ConsentToggles;
