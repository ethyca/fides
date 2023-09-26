import { h, FunctionComponent } from "preact";
import { useState, useCallback, useMemo } from "preact/hooks";
import {
  ConsentMechanism,
  ConsentMethod,
  PrivacyNotice,
  SaveConsentPreference,
} from "../../lib/consent-types";
import ConsentBanner from "../ConsentBanner";

import { updateConsentPreferences } from "../../lib/preferences";
import {
  debugLog,
  hasActionNeededNotices,
  transformConsentToFidesUserPreference,
} from "../../lib/consent-utils";

import "../fides.css";
import Overlay from "../Overlay";
import { NoticeConsentButtons } from "../ConsentButtons";
import NoticeToggles from "./NoticeToggles";
import { OverlayProps } from "../types";
import { useConsentServed } from "../../lib/hooks";

const NoticeOverlay: FunctionComponent<OverlayProps> = ({
  experience,
  options,
  fidesRegionString,
  cookie,
}) => {
  const initialEnabledNoticeKeys = useMemo(
    () => Object.keys(cookie.consent).filter((key) => cookie.consent[key]),
    [cookie.consent]
  );

  const [draftEnabledNoticeKeys, setDraftEnabledNoticeKeys] = useState<
    Array<PrivacyNotice["notice_key"]>
  >(initialEnabledNoticeKeys);

  const showBanner = useMemo(
    () => experience.show_banner && hasActionNeededNotices(experience),
    [experience]
  );

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

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }
  const experienceConfig = experience.experience_config;

  return (
    <Overlay
      options={options}
      experience={experience}
      cookie={cookie}
      renderBanner={({ isOpen, onClose, onSave, onManagePreferencesClick }) =>
        showBanner ? (
          <ConsentBanner
            bannerIsOpen={isOpen}
            onClose={onClose}
            experience={experienceConfig}
          >
            <NoticeConsentButtons
              experience={experience}
              onManagePreferencesClick={onManagePreferencesClick}
              enabledKeys={draftEnabledNoticeKeys}
              onSave={(keys) => {
                handleUpdatePreferences(keys);
                onSave();
              }}
              isAcknowledge={isAllNoticeOnly}
            />
          </ConsentBanner>
        ) : null
      }
      renderModalContent={({ onClose }) => (
        <div>
          <div className="fides-modal-notices">
            <NoticeToggles
              notices={privacyNotices}
              enabledNoticeKeys={draftEnabledNoticeKeys}
              onChange={setDraftEnabledNoticeKeys}
            />
          </div>
          <NoticeConsentButtons
            experience={experience}
            enabledKeys={draftEnabledNoticeKeys}
            onSave={(keys) => {
              handleUpdatePreferences(keys);
              onClose();
            }}
            isInModal
            isAcknowledge={isAllNoticeOnly}
          />
        </div>
      )}
    />
  );
};

export default NoticeOverlay;
