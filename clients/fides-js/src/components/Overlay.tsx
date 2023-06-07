import { h, FunctionComponent } from "preact";
import { useEffect, useState } from "preact/hooks";
import { useCallback } from "react";
import {
  ConsentMethod,
  FidesOptions,
  PrivacyExperience,
  PrivacyNotice,
  SaveConsentPreference,
} from "../lib/consent-types";
import ConsentBanner from "./ConsentBanner";

import { updateConsentPreferences } from "../lib/preferences";
import {
  debugLog,
  transformConsentToFidesUserPreference,
} from "../lib/consent-utils";
import { FidesCookie } from "../lib/cookie";

import "./fides.css";
import { useA11yDialog } from "../lib/a11y-dialog";
import ConsentModal from "./ConsentModal";

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
  const [bannerIsOpen, setBannerIsOpen] = useState(false);
  const { instance, attributes } = useA11yDialog({
    id: "fides-modal",
    role: "dialog",
    title: experience?.experience_config?.title || "",
  });

  const handleOpenModal = useCallback(() => {
    if (instance) {
      instance.show();
    }
  }, [instance]);

  const handleCloseModal = useCallback(() => {
    if (instance) {
      instance.hide();
    }
  }, [instance]);

  useEffect(() => {
    const delayBanner = setTimeout(() => {
      setBannerIsOpen(true);
    }, 100);
    return () => clearTimeout(delayBanner);
  }, [setBannerIsOpen]);

  useEffect(() => {
    if (modalLinkEl) {
      debugLog(
        options.debug,
        "Modal link element found, updating it to show and trigger modal on click."
      );
      // Update modal link to trigger modal on click
      const modalLink = modalLinkEl;
      modalLink.onclick = () => {
        handleOpenModal();
        setBannerIsOpen(false);
      };
      // Update to show the pre-existing modal link in the DOM
      modalLink.classList.add("fides-modal-link-shown");
    } else {
      debugLog(options.debug, "Modal link element not found.");
    }
  }, [modalLinkEl, options.debug, handleOpenModal]);

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
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
    setBannerIsOpen(false);
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
    setBannerIsOpen(false);
  };

  const handleManagePreferencesClick = (): void => {
    handleOpenModal();
    setBannerIsOpen(false);
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
      {experience.show_banner ? (
        <ConsentBanner
          experience={experience.experience_config}
          onAcceptAll={onAcceptAll}
          onRejectAll={onRejectAll}
          onManagePreferences={handleManagePreferencesClick}
          bannerIsOpen={bannerIsOpen}
          onClose={() => {
            setBannerIsOpen(false);
          }}
        />
      ) : null}
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
