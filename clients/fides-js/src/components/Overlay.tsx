import { h, FunctionComponent } from "preact";
import { useEffect, useState, useCallback, useMemo } from "preact/hooks";
import {
  ConsentMechanism,
  ConsentMethod,
  FidesOptions,
  PrivacyExperience,
  PrivacyNotice,
  SaveConsentPreference,
  ServingComponent,
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
import { useConsentServed, useHasMounted } from "../lib/hooks";
import ConsentButtons from "./ConsentButtons";
import { dispatchFidesEvent } from "../lib/events";

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
    () => Object.keys(cookie.consent).filter((key) => cookie.consent[key]),
    [cookie.consent]
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
      dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
        servingComponent: ServingComponent.OVERLAY,
      });
    }
  }, [instance, cookie, options.debug]);

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

  useEffect(() => {
    if (showBanner && bannerIsOpen) {
      dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
        servingComponent: ServingComponent.BANNER,
      });
    }
  }, [showBanner, cookie, options.debug, bannerIsOpen]);

  const privacyNotices = useMemo(
    () => experience.privacy_notices ?? [],
    [experience.privacy_notices]
  );

  const isAllNoticeOnly = privacyNotices.every(
    (n) => n.consent_mechanism === ConsentMechanism.NOTICE_ONLY
  );

  const { servedNotices } = useConsentServed({
    notices: privacyNotices,
    options,
    userGeography: fidesRegionString,
    acknowledgeMode: isAllNoticeOnly,
    privacyExperienceId: experience.id,
  });

  const handleUpdatePreferences = useCallback(
    (enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>) => {
      const consentPreferencesToSave = privacyNotices.map((notice) => {
        const userPreference = transformConsentToFidesUserPreference(
          enabledPrivacyNoticeKeys.includes(notice.notice_key),
          notice.consent_mechanism
        );
        return new SaveConsentPreference(notice, userPreference);
      });
      updateConsentPreferences({
        consentPreferencesToSave,
        experienceId: experience.id,
        fidesApiUrl: options.fidesApiUrl,
        consentMethod: ConsentMethod.button,
        userLocationString: fidesRegionString,
        cookie,
        servedNotices,
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
      servedNotices,
    ]
  );

  const handleManagePreferencesClick = (): void => {
    handleOpenModal();
    setBannerIsOpen(false);
  };

  if (!hasMounted) {
    return null;
  }

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }

  return (
    <div>
      {showBanner ? (
        <ConsentBanner
          experience={experience.experience_config}
          bannerIsOpen={bannerIsOpen}
          onClose={() => {
            setBannerIsOpen(false);
          }}
          buttonGroup={
            <ConsentButtons
              experience={experience}
              onManagePreferencesClick={handleManagePreferencesClick}
              enabledKeys={draftEnabledNoticeKeys}
              onSave={(keys) => {
                handleUpdatePreferences(keys);
                setBannerIsOpen(false);
              }}
              isAcknowledge={isAllNoticeOnly}
            />
          }
        />
      ) : null}
      <ConsentModal
        attributes={attributes}
        experience={experience.experience_config}
        enabledNoticeKeys={draftEnabledNoticeKeys}
        onChange={setDraftEnabledNoticeKeys}
        notices={privacyNotices}
        onClose={handleCloseModal}
        buttonGroup={
          <ConsentButtons
            experience={experience}
            enabledKeys={draftEnabledNoticeKeys}
            isInModal
            onSave={(keys) => {
              handleUpdatePreferences(keys);
              handleCloseModal();
            }}
            isAcknowledge={isAllNoticeOnly}
          />
        }
        options={options}
      />
    </div>
  );
};

export default Overlay;
