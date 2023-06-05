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
import {
  debugLog,
  transformConsentToFidesUserPreference,
} from "../lib/consent-utils";
import { FidesCookie } from "../lib/cookie";

import "./fides.css";

export interface OverlayProps {
  options: FidesOptions;
  experience: PrivacyExperience;
  cookie: FidesCookie;
  fidesRegionString: string;
  modalLinkEl?: HTMLElement | null;
}

const Overlay: FunctionComponent<OverlayProps> = ({
  experience,
  options,
  fidesRegionString,
  cookie,
  modalLinkEl,
}) => {
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const [bannerIsOpen, setBannerIsOpen] = useState(false);

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }

  const privacyNotices = experience.privacy_notices ?? [];

  if (modalLinkEl) {
    debugLog(
      options.debug,
      "Modal link element found, updating it to show and trigger modal on click."
    );
    // Update modal link to trigger modal on click
    const modalLink = modalLinkEl;
    modalLink.onclick = () => {
      setModalIsOpen(true);
      setBannerIsOpen(false);
    };
    // Update to show the pre-existing modal link in the DOM
    modalLink.style.display = "inline";
  } else {
    debugLog(options.debug, "Modal link element not found.");
  }

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
      {experience.show_banner ? (
        <ConsentBanner
          experience={experience.experience_config}
          onAcceptAll={onAcceptAll}
          onRejectAll={onRejectAll}
          waitBeforeShow={100}
          onOpenModal={() => setModalIsOpen(true)}
          bannerIsOpen={bannerIsOpen}
          setBannerIsOpen={setBannerIsOpen}
        />
      ) : null}
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
