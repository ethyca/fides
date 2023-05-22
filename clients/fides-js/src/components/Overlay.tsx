import { FunctionComponent, h } from "preact";
import { useState } from "preact/hooks";
import {
  PrivacyExperience,
  FidesOptions,
  PrivacyNotice,
  UserGeolocation,
} from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";
import { CookieKeyConsent } from "../lib/cookie";
import ConsentModal from "./ConsentModal";

import { updateConsentPreferences } from "../lib/preferences";

export interface OverlayProps {
  consentDefaults: CookieKeyConsent;
  options: FidesOptions;
  experience?: PrivacyExperience;
  geolocation?: UserGeolocation;
}

const Overlay: FunctionComponent<OverlayProps> = ({ experience }) => {
  const [modalIsOpen, setModalIsOpen] = useState(false);

  if (!experience) {
    return null;
  }
  const privacyNotices = experience.privacy_notices ?? [];

  const onAcceptAll = () => {
    const allNoticeIds = privacyNotices.map((notice) => notice.id);
    updateConsentPreferences({
      privacyNotices,
      enabledPrivacyNoticeIds: allNoticeIds,
    });
  };

  const onRejectAll = () => {
    updateConsentPreferences({ privacyNotices, enabledPrivacyNoticeIds: [] });
  };

  const onSavePreferences = (
    enabledPrivacyNoticeIds: Array<PrivacyNotice["id"]>
  ) => {
    updateConsentPreferences({
      privacyNotices,
      enabledPrivacyNoticeIds,
    });
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
