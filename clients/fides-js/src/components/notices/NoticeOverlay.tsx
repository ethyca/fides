import { h, FunctionComponent } from "preact";
import { useState, useCallback, useMemo } from "preact/hooks";
import {
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

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }
  const experienceConfig = experience.experience_config;

  return (
    <Overlay
      options={options}
      experience={experience}
      renderBanner={({ isOpen, onClose, onSave, onManagePreferencesClick }) =>
        showBanner ? (
          <ConsentBanner
            bannerIsOpen={isOpen}
            onClose={onClose}
            experience={experienceConfig}
            buttonGroup={
              <NoticeConsentButtons
                experience={experience}
                onManagePreferencesClick={onManagePreferencesClick}
                enabledKeys={draftEnabledNoticeKeys}
                onSave={(keys) => {
                  handleUpdatePreferences(keys);
                  onSave();
                }}
              />
            }
          />
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
          />
        </div>
      )}
    />
  );
};

export default NoticeOverlay;
