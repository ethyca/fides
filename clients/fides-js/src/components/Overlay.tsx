import { h, FunctionComponent } from "preact";
import { useState } from "preact/hooks";
import {
  ConsentMethod,
  FidesOptions,
  PrivacyExperience,
  PrivacyNotice,
} from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";
import ConsentModal from "./ConsentModal";

import { updateConsentPreferences } from "../lib/preferences";

export interface OverlayProps {
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
    const allNoticeKeys = privacyNotices.map((notice) => notice.notice_key);
    updateConsentPreferences({
      privacyNotices,
      experienceHistoryId: experience.privacy_experience_history_id,
      enabledPrivacyNoticeKeys: allNoticeKeys,
      fidesApiUrl: options.fidesApiUrl,
      consentMethod: ConsentMethod.button,
      userLocationString: fidesRegionString,
    });
  };

  const onRejectAll = () => {
    updateConsentPreferences({
      privacyNotices,
      experienceHistoryId: experience.privacy_experience_history_id,
      enabledPrivacyNoticeKeys: [],
      fidesApiUrl: options.fidesApiUrl,
      consentMethod: ConsentMethod.button,
      userLocationString: fidesRegionString,
    });
  };

  const onSavePreferences = (
    enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>
  ) => {
    updateConsentPreferences({
      privacyNotices,
      experienceHistoryId: experience.privacy_experience_history_id,
      enabledPrivacyNoticeKeys,
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
