import { h } from "preact";
import { FidesConfig } from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";
import { getConsentContext } from "../lib/consent-context";
import {
  makeConsentDefaults,
  setConsentCookieAcceptAll,
  setConsentCookieRejectAll,
} from "../lib/cookie";

const App = ({ config }: { config: FidesConfig }) => {
  const context = getConsentContext();
  const consentDefaults = makeConsentDefaults({
    config: config.consent,
    context,
  });

  const onAcceptAll = () => {
    setConsentCookieAcceptAll(consentDefaults);
  };

  const onRejectAll = () => {
    setConsentCookieRejectAll(consentDefaults);
  };

  return (
    <ConsentBanner
      bannerTitle={config.experience?.banner_title}
      bannerDescription={config.experience?.banner_description}
      confirmationButtonLabel={config.experience?.confirmation_button_label}
      rejectButtonLabel={config.experience?.reject_button_label}
      privacyCenterUrl={config.options.privacyCenterUrl}
      onAcceptAll={onAcceptAll}
      onRejectAll={onRejectAll}
      waitBeforeShow={100}
    />
  );
};

export default App;
