import { h, FunctionComponent } from "preact";
import {
  ConsentMethod,
  FidesOptions,
  PrivacyExperience,
  PrivacyNotice,
  SaveConsentPreference,
} from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";

import { updateConsentPreferences } from "../lib/preferences";
import { transformConsentToFidesUserPreference } from "../lib/consent-utils";
import { FidesCookie } from "../lib/cookie";

import "./fides.css";
import { useA11yDialog } from "../lib/a11y-dialog";
import ConsentModal from "./ConsentModal";

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
  const { instance, attributes } = useA11yDialog({
    id: "fides-modal",
    role: "dialog",
    title: experience?.experience_config?.title || "",
  });

  const handleOpenModal = () => {
    if (instance) {
      instance.show();
    }
  };

  const handleCloseModal = () => {
    if (instance) {
      instance.hide();
    }
  };

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
      experienceHistoryId: experience.privacy_experience_history_id,
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
      experienceHistoryId: experience.privacy_experience_history_id,
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
      experienceHistoryId: experience.privacy_experience_history_id,
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
        onOpenModal={handleOpenModal}
      />
      <ConsentModal
        attributes={attributes}
        experience={experience.experience_config}
        notices={privacyNotices}
        onClose={handleCloseModal}
        onAcceptAll={onAcceptAll}
        onRejectAll={onRejectAll}
        onSave={onSavePreferences}
      />
    </div>
  );
};

export default Overlay;
