import { FunctionComponent, h } from "preact";
import {
  PrivacyExperience,
  FidesOptions,
  UserGeolocation,
} from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";
import {
  CookieKeyConsent,
  setConsentCookieAcceptAll,
  setConsentCookieRejectAll,
} from "../lib/cookie";

export interface OverlayProps {
  consentDefaults: CookieKeyConsent;
  options: FidesOptions;
  experience?: PrivacyExperience;
  geolocation?: UserGeolocation;
}

const Overlay: FunctionComponent<OverlayProps> = ({
  consentDefaults,
  experience,
  options,
}) => {
  const onAcceptAll = () => {
    setConsentCookieAcceptAll(consentDefaults);
    // TODO: save to Fides consent request API
    // eslint-disable-next-line no-console
    console.error(
      "Could not save consent record to Fides API, not implemented!"
    );
  };

  const onRejectAll = () => {
    setConsentCookieRejectAll(consentDefaults);
    // TODO: save to Fides consent request API
    // eslint-disable-next-line no-console
    console.error(
      "Could not save consent record to Fides API, not implemented!"
    );
  };

  return (
    <ConsentBanner
      bannerTitle={experience?.experience_config?.banner_title}
      bannerDescription={experience?.experience_config?.banner_description}
      confirmationButtonLabel={experience?.experience_config?.confirmation_button_label}
      rejectButtonLabel={experience?.experience_config?.reject_button_label}
      privacyCenterUrl={options.privacyCenterUrl}
      onAcceptAll={onAcceptAll}
      onRejectAll={onRejectAll}
    />
  );
};

export default Overlay;
