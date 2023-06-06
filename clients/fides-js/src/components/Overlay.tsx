import { h, FunctionComponent } from "preact";
import { useState } from "preact/hooks";
import {
  ConsentMethod,
  FidesOptions,
  PrivacyExperience,
  PrivacyNotice,
  SaveConsentPreference,
} from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";
import ConsentModal from "./ConsentModal";

import { updateConsentPreferences } from "../lib/preferences";
import { transformConsentToFidesUserPreference } from "../lib/consent-utils";
import { FidesCookie } from "../lib/cookie";

import "./fides.css";

export interface OverlayProps {
  options: FidesOptions;
  experience: PrivacyExperience;
  cookie: FidesCookie;
  fidesRegionString: string;
}

const Overlay: FunctionComponent<OverlayProps> = ({
  experience,
  options,
  fidesRegionString,
  cookie,
}) => {
  const [modalIsOpen, setModalIsOpen] = useState(false);

  if (!experience.experience_config) {
    return null;
  }

  const privacyNotices = experience.privacy_notices ?? [];

  const onAcceptAll = () => {
    const consentPreferencesToSave: Array<SaveConsentPreference> = [];
    privacyNotices.forEach((notice) => {
      consentPreferencesToSave.push(
        new SaveConsentPreference(
          notice.notice_key,
          notice.privacy_notice_history_id,
          transformConsentToFidesUserPreference(true, notice.consent_mechanism)
        )
      );
    });
    updateConsentPreferences({
      consentPreferencesToSave,
      experienceId: experience.id,
      fidesApiUrl: options.fidesApiUrl,
      consentMethod: ConsentMethod.button,
      userLocationString: fidesRegionString,
      cookie,
    });
  };

  const onRejectAll = () => {
    const consentPreferencesToSave: Array<SaveConsentPreference> = [];
    privacyNotices.forEach((notice) => {
      consentPreferencesToSave.push(
        new SaveConsentPreference(
          notice.notice_key,
          notice.privacy_notice_history_id,
          transformConsentToFidesUserPreference(false, notice.consent_mechanism)
        )
      );
    });
    updateConsentPreferences({
      consentPreferencesToSave,
      experienceId: experience.id,
      fidesApiUrl: options.fidesApiUrl,
      consentMethod: ConsentMethod.button,
      userLocationString: fidesRegionString,
      cookie,
    });
  };

  const onSavePreferences = (
    enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>
  ) => {
    const consentPreferencesToSave: Array<SaveConsentPreference> = [];
    privacyNotices.forEach((notice) => {
      consentPreferencesToSave.push(
        new SaveConsentPreference(
          notice.notice_key,
          notice.privacy_notice_history_id,
          transformConsentToFidesUserPreference(
            enabledPrivacyNoticeKeys.includes(notice.notice_key),
            notice.consent_mechanism
          )
        )
      );
    });
    updateConsentPreferences({
      consentPreferencesToSave,
      experienceId: experience.id,
      fidesApiUrl: options.fidesApiUrl,
      consentMethod: ConsentMethod.button,
      userLocationString: fidesRegionString,
      cookie,
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
