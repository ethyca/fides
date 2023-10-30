import { h, FunctionComponent, Fragment } from "preact";
import { useState, useCallback, useMemo } from "preact/hooks";
import {
  ConsentMechanism,
  ConsentMethod,
  LastServedConsentSchema,
  PrivacyNotice,
  SaveConsentPreference,
  ServingComponent,
} from "../../lib/consent-types";
import ConsentBanner from "../ConsentBanner";

import { updateConsentPreferences } from "../../lib/preferences";
import {
  debugLog,
  transformConsentToFidesUserPreference,
} from "../../lib/consent-utils";

import "../fides.css";
import Overlay from "../Overlay";
import { NoticeConsentButtons } from "../ConsentButtons";
import NoticeToggles from "./NoticeToggles";
import { OverlayProps } from "../types";
import { useConsentServed } from "../../lib/hooks";
import { updateCookieFromNoticePreferences } from "../../lib/cookie";
import PrivacyPolicyLink from "../PrivacyPolicyLink";
import { dispatchFidesEvent } from "../../lib/events";

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
    privacyExperience: experience,
  });

  const createConsentPreferencesToSave = (
    privacyNoticeList: PrivacyNotice[],
    enabledPrivacyNoticeKeys: string[],
    servedNoticeList: LastServedConsentSchema[]
  ): SaveConsentPreference[] => {
    const servedNoticeMap = Object.fromEntries(
      servedNoticeList
        .filter((notice) => notice.privacy_notice_history?.id !== undefined)
        .map((notice) => [
          notice.privacy_notice_history?.id,
          notice.served_notice_history_id,
        ])
    );

    return privacyNoticeList.map((notice) => {
      const userPreference = transformConsentToFidesUserPreference(
        enabledPrivacyNoticeKeys.includes(notice.notice_key),
        notice.consent_mechanism
      );
      return new SaveConsentPreference(
        notice,
        userPreference,
        servedNoticeMap[notice.privacy_notice_history_id]
      );
    });
  };

  const handleUpdatePreferences = useCallback(
    (enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>) => {
      const consentPreferencesToSave = createConsentPreferencesToSave(
        privacyNotices,
        enabledPrivacyNoticeKeys,
        servedNotices
      );

      updateConsentPreferences({
        consentPreferencesToSave,
        experience,
        consentMethod: ConsentMethod.button,
        options,
        userLocationString: fidesRegionString,
        cookie,
        updateCookie: (oldCookie) =>
          updateCookieFromNoticePreferences(
            oldCookie,
            consentPreferencesToSave
          ),
      });
      // Make sure our draft state also updates
      setDraftEnabledNoticeKeys(enabledPrivacyNoticeKeys);
    },
    [
      privacyNotices,
      cookie,
      fidesRegionString,
      experience,
      options,
      servedNotices,
    ]
  );

  const dispatchOpenBannerEvent = useCallback(() => {
    dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
      servingComponent: ServingComponent.BANNER,
    });
  }, [cookie, options.debug]);

  const dispatchOpenOverlayEvent = useCallback(() => {
    dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
      servingComponent: ServingComponent.OVERLAY,
    });
  }, [cookie, options.debug]);

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
      onOpen={dispatchOpenOverlayEvent}
      renderBanner={({ isOpen, onClose, onSave, onManagePreferencesClick }) => (
        <ConsentBanner
          bannerIsOpen={isOpen}
          onOpen={dispatchOpenBannerEvent}
          onClose={onClose}
          experience={experienceConfig}
          renderButtonGroup={({ isMobile }) => (
            <NoticeConsentButtons
              experience={experience}
              onManagePreferencesClick={onManagePreferencesClick}
              enabledKeys={draftEnabledNoticeKeys}
              onSave={(keys) => {
                handleUpdatePreferences(keys);
                onSave();
              }}
              isAcknowledge={isAllNoticeOnly}
              middleButton={<PrivacyPolicyLink experience={experienceConfig} />}
              isMobile={isMobile}
            />
          )}
        />
      )}
      renderModalContent={() => (
        <div>
          <div className="fides-modal-notices">
            <NoticeToggles
              notices={privacyNotices}
              enabledNoticeKeys={draftEnabledNoticeKeys}
              onChange={(updatedKeys) => {
                setDraftEnabledNoticeKeys(updatedKeys);
                dispatchFidesEvent("FidesUIChanged", cookie, options.debug);
              }}
            />
          </div>
        </div>
      )}
      renderModalFooter={({ onClose, isMobile }) => (
        <Fragment>
          <NoticeConsentButtons
            experience={experience}
            enabledKeys={draftEnabledNoticeKeys}
            onSave={(keys) => {
              handleUpdatePreferences(keys);
              onClose();
            }}
            isInModal
            isAcknowledge={isAllNoticeOnly}
            isMobile={isMobile}
          />
          <PrivacyPolicyLink experience={experience.experience_config} />
        </Fragment>
      )}
    />
  );
};

export default NoticeOverlay;
