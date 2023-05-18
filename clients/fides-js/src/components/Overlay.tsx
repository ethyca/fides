import { FunctionComponent, h } from "preact";
import { useState } from "preact/hooks";
import {
  ExperienceConfig,
  FidesOptions,
  PrivacyNotice,
  UserGeolocation,
} from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";
import {
  CookieKeyConsent,
  setConsentCookieFromPrivacyNotices,
} from "../lib/cookie";
import ConsentModal from "./ConsentModal";
import { debugLog } from "../lib/consent-utils";

export interface OverlayProps {
  consentDefaults: CookieKeyConsent;
  options: FidesOptions;
  experience?: ExperienceConfig;
  geolocation?: UserGeolocation;
}

const Overlay: FunctionComponent<OverlayProps> = ({ experience, options }) => {
  const [modalIsOpen, setModalIsOpen] = useState(false);

  if (!experience) {
    return null;
  }
  const privacyNotices = experience.privacy_notices ?? [];

  const mockPatch = () => {
    // TODO: save to Fides consent request API
    // eslint-disable-next-line no-console
    console.error(
      "Could not save consent record to Fides API, not implemented!"
    );
  };

  const onAcceptAll = () => {
    const allNoticeIds = privacyNotices.map((notice) => notice.id);
    setConsentCookieFromPrivacyNotices({
      privacyNotices,
      enabledPrivacyNoticeIds: allNoticeIds,
    });
    mockPatch();
  };

  const onRejectAll = () => {
    setConsentCookieFromPrivacyNotices({
      privacyNotices,
      enabledPrivacyNoticeIds: [],
    });
    mockPatch();
  };

  const onSavePreferences = (
    enabledPrivacyNoticeIds: Array<PrivacyNotice["id"]>
  ) => {
    debugLog(options.debug, enabledPrivacyNoticeIds);
    setConsentCookieFromPrivacyNotices({
      privacyNotices,
      enabledPrivacyNoticeIds,
    });
    mockPatch();
  };

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
