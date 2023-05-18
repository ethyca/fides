import { FunctionComponent, h } from "preact";
import { useState } from "preact/hooks";
import {
  ExperienceConfig,
  FidesOptions,
  UserGeolocation,
} from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";
import {
  CookieKeyConsent,
  setConsentCookieAcceptAll,
  setConsentCookieRejectAll,
} from "../lib/cookie";
import ConsentModal from "./ConsentModal";
import { debugLog } from "../lib/consent-utils";

export interface OverlayProps {
  consentDefaults: CookieKeyConsent;
  options: FidesOptions;
  experience?: ExperienceConfig;
  geolocation?: UserGeolocation;
}

const Overlay: FunctionComponent<OverlayProps> = ({
  consentDefaults,
  experience,
  options,
}) => {
  const [modalIsOpen, setModalIsOpen] = useState(false);
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

  // DEFER: properly type this payload and implement fetch PATCH
  // against /consent-request/id/privacy-preferences?
  const onSavePreferences = (payload: any) => {
    debugLog(options.debug, payload);
  };

  if (!experience) {
    return null;
  }
  const privacyNotices = experience.privacy_notices ?? [];

  return (
    <div id="fides-js-root">
      <ConsentBanner
        experience={experience}
        onAcceptAll={onAcceptAll}
        onRejectAll={onRejectAll}
        waitBeforeShow={100}
        onOpenModal={() => setModalIsOpen(true)}
      />
      {modalIsOpen ? (
        <ConsentModal
          experience={experience}
          notices={privacyNotices}
          onClose={() => setModalIsOpen(false)}
          onAcceptAll={onAcceptAll}
          onRejectAll={onRejectAll}
          onSave={onSavePreferences}
        />
      ) : null}
    </div>
  );
};

export default Overlay;
