import { h, FunctionComponent } from "preact";
import { useEffect, useState, useCallback, useMemo } from "preact/hooks";
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
  hasActionNeededNotices,
  transformConsentToFidesUserPreference,
} from "../lib/consent-utils";
import { FidesCookie } from "../lib/cookie";

import "./fides.css";
import { useA11yDialog } from "../lib/a11y-dialog";
import ConsentModal from "./ConsentModal";
import { useHasMounted } from "../lib/hooks";

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
  const hasMounted = useHasMounted();
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

  const showBanner = useMemo(
    () => experience.show_banner && hasActionNeededNotices(experience),
    [experience]
  );

  const privacyNotices = useMemo(
    () => experience.privacy_notices ?? [],
    [experience.privacy_notices]
  );

  const handleUpdatePreferences = useCallback(
    ({
      noticeKeyToConsent,
    }: {
      noticeKeyToConsent: (noticeKey: string) => boolean;
    }) => {
      const consentPreferencesToSave = privacyNotices.map((notice) => {
        const consent = noticeKeyToConsent(notice.notice_key);
        const userPreference = transformConsentToFidesUserPreference(
          consent,
          notice.consent_mechanism
        );
        return new SaveConsentPreference(
          notice.notice_key,
          notice.privacy_notice_history_id,
          userPreference
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
    },
    [
      privacyNotices,
      cookie,
      fidesRegionString,
      experience.id,
      options.fidesApiUrl,
    ]
  );

  if (!hasMounted) {
    return null;
  }

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }

  const onAcceptAll = () => {
    handleUpdatePreferences({ noticeKeyToConsent: () => true });
    setBannerIsOpen(false);
  };

  const onRejectAll = () => {
    handleUpdatePreferences({ noticeKeyToConsent: () => false });
    setBannerIsOpen(false);
  };

  const onSavePreferences = (
    enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>
  ) => {
    handleUpdatePreferences({
      noticeKeyToConsent: (noticeKey) =>
        enabledPrivacyNoticeKeys.includes(noticeKey),
    });
  };

  const handleManagePreferencesClick = (): void => {
    handleOpenModal();
    setBannerIsOpen(false);
  };

  return (
    <div id="fides-js-root">
      {showBanner ? (
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
