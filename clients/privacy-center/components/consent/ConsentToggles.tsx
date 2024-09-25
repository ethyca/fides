import { useSettings } from "~/features/common/settings.slice";
import { ConsentPreferences } from "~/types/api";

import ConfigDrivenConsent from "./ConfigDrivenConsent";
import NoticeDrivenConsent from "./notice-driven/NoticeDrivenConsent";

const ConsentToggles = ({
  storePreferences,
}: {
  storePreferences: (data: ConsentPreferences) => void;
}) => {
  const settings = useSettings();
  const { IS_OVERLAY_ENABLED, BASE_64_COOKIE } = settings;

  if (IS_OVERLAY_ENABLED) {
    return <NoticeDrivenConsent base64Cookie={BASE_64_COOKIE} />;
  }
  return (
    <ConfigDrivenConsent
      storePreferences={storePreferences}
      base64Cookie={BASE_64_COOKIE}
    />
  );
};

export default ConsentToggles;
