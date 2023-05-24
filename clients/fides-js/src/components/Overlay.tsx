import { h, FunctionComponent } from "preact";
import { useState } from "preact/hooks";
import {
  ConsentMethod,
  FidesOptions,
  PrivacyExperience,
  PrivacyNotice,
} from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";
import { CookieKeyConsent } from "../lib/cookie";
import ConsentModal from "./ConsentModal";

import { updateConsentPreferences } from "../lib/preferences";

export interface OverlayProps {
  consentDefaults: CookieKeyConsent;
  options: FidesOptions;
  experience: PrivacyExperience;
  fidesRegionString: string;
}

const Overlay: FunctionComponent<OverlayProps> = ({
  experience,
  options,
  fidesRegionString,
}) => {
  const [modalIsOpen, setModalIsOpen] = useState(false);

  if (!experience.experience_config) {
    return null;
  }

  const privacyNotices = experience.privacy_notices ?? [];

  const onAcceptAll = () => {
    const allNoticeIds = privacyNotices.map((notice) => notice.id);
    updateConsentPreferences({
      privacyNotices,
      experienceHistoryId: experience.privacy_experience_history_id,
      enabledPrivacyNoticeIds: allNoticeIds,
      fidesApiUrl: options.fidesApiUrl,
      consentMethod: ConsentMethod.button,
      userLocationString: fidesRegionString,
    });
  };

  const onRejectAll = () => {
    updateConsentPreferences({
      privacyNotices,
      experienceHistoryId: experience.privacy_experience_history_id,
      enabledPrivacyNoticeIds: [],
      fidesApiUrl: options.fidesApiUrl,
      consentMethod: ConsentMethod.button,
      userLocationString: fidesRegionString,
    });
  };

  const onSavePreferences = (
    enabledPrivacyNoticeIds: Array<PrivacyNotice["id"]>
  ) => {
    updateConsentPreferences({
      privacyNotices,
      experienceHistoryId: experience.privacy_experience_history_id,
      enabledPrivacyNoticeIds,
      fidesApiUrl: options.fidesApiUrl,
      consentMethod: ConsentMethod.button,
      userLocationString: fidesRegionString,
    });
  };

  return (
    <div id="fides-js-root">
      <ConsentBanner
        experience={experience.experience_config}
        onAcceptAll={onAcceptAll}
        onRejectAll={onRejectAll}
        waitBeforeShow={100}
        onOpenModal={() => setModalIsOpen(true)}
      />
      {modalIsOpen ? (
        <ConsentModal
          experience={experience.experience_config}
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
