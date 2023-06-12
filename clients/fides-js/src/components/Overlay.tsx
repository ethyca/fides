import { h, FunctionComponent } from "preact";
import { useEffect, useState, useCallback, useMemo } from "preact/hooks";
import {
  ConsentMechanism,
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
}

const Overlay: FunctionComponent<OverlayProps> = ({
  experience,
  options,
  fidesRegionString,
  cookie,
}) => {
  const delayBannerMilliseconds = 100;
  const delayModalLinkMilliseconds = 200;
  const hasMounted = useHasMounted();
  const [bannerIsOpen, setBannerIsOpen] = useState(false);

  const initialEnabledNoticeKeys = useMemo(
    () =>
      Object.keys(window.Fides.consent).filter(
        (key) => window.Fides.consent[key]
      ),
    []
  );
  const [draftEnabledNoticeKeys, setDraftEnabledNoticeKeys] = useState<
    Array<PrivacyNotice["notice_key"]>
  >(initialEnabledNoticeKeys);

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
    }, delayBannerMilliseconds);
    return () => clearTimeout(delayBanner);
  }, [setBannerIsOpen]);

  useEffect(() => {
    // use a delay to ensure that link exists in the DOM
    const delayModalLinkBinding = setTimeout(() => {
      const modalLinkId = options.modalLinkId || "fides-modal-link";
      const modalLinkEl = document.getElementById(modalLinkId);
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
    }, delayModalLinkMilliseconds);
    return () => clearTimeout(delayModalLinkBinding);
  }, [options.modalLinkId, options.debug, handleOpenModal]);

  const showBanner = useMemo(
    () => experience.show_banner && hasActionNeededNotices(experience),
    [experience]
  );

  const privacyNotices = useMemo(
    () => experience.privacy_notices ?? [],
    [experience.privacy_notices]
  );

  const handleUpdatePreferences = useCallback(
    (enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>) => {
      const consentPreferencesToSave = privacyNotices.map((notice) => {
        const userPreference = transformConsentToFidesUserPreference(
          enabledPrivacyNoticeKeys.includes(notice.notice_key),
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
      // Make sure our draft state also updates
      setDraftEnabledNoticeKeys(enabledPrivacyNoticeKeys);
    },
    [
      privacyNotices,
      cookie,
      fidesRegionString,
      experience.id,
      options.fidesApiUrl,
    ]
  );

  const handleManagePreferencesClick = (): void => {
    handleOpenModal();
    setBannerIsOpen(false);
  };

  const handleAcceptAll = () => {
    handleUpdatePreferences(privacyNotices.map((n) => n.notice_key));
  };
  const handleRejectAll = () => {
    handleUpdatePreferences(
      privacyNotices
        .filter((n) => n.consent_mechanism === ConsentMechanism.NOTICE_ONLY)
        .map((n) => n.notice_key)
    );
  };

  if (!hasMounted) {
    return null;
  }

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }

  const isAllNoticeOnly = privacyNotices.every(
    (n) => n.consent_mechanism === ConsentMechanism.NOTICE_ONLY
  );

  return (
    <div>
      {showBanner ? (
        <ConsentBanner
          experience={experience.experience_config}
          onAcceptAll={handleAcceptAll}
          onRejectAll={handleRejectAll}
          onManagePreferences={handleManagePreferencesClick}
          bannerIsOpen={bannerIsOpen}
          onClose={() => {
            setBannerIsOpen(false);
          }}
          showAcknowledge={isAllNoticeOnly}
        />
      ) : null}
      <ConsentModal
        attributes={attributes}
        experience={experience.experience_config}
        enabledNoticeKeys={draftEnabledNoticeKeys}
        onChange={setDraftEnabledNoticeKeys}
        notices={privacyNotices}
        onClose={handleCloseModal}
        onAcceptAll={handleAcceptAll}
        onRejectAll={handleRejectAll}
        onSave={handleUpdatePreferences}
      />
    </div>
  );
};

export default Overlay;
