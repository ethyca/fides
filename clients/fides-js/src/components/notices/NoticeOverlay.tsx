import { h, Fragment, FunctionComponent } from "preact";
import { useCallback, useMemo, useState } from "preact/hooks";
import {
  ConsentMechanism,
  ConsentMethod,
  FidesCookie,
  PrivacyNotice,
  SaveConsentPreference,
  ServingComponent,
} from "../../lib/consent-types";
import ConsentBanner from "../ConsentBanner";

import { updateConsentPreferences } from "../../lib/preferences";
import { debugLog } from "../../lib/consent-utils";

import "../fides.css";
import Overlay from "../Overlay";
import { NoticeConsentButtons } from "../ConsentButtons";
import NoticeToggles from "./NoticeToggles";
import { OverlayProps } from "../types";
import { useConsentServed } from "../../lib/hooks";
import {
  getFidesConsentCookie,
  updateCookieFromNoticePreferences,
} from "../../lib/cookie";
import PrivacyPolicyLink from "../PrivacyPolicyLink";
import { dispatchFidesEvent } from "../../lib/events";
import { resolveConsentValue } from "../../lib/consent-value";
import { getConsentContext } from "../../lib/consent-context";
import { transformConsentToFidesUserPreference } from "../../lib/shared-consent-utils";

const NoticeOverlay: FunctionComponent<OverlayProps> = ({
  options,
  experience,
  i18n,
  fidesRegionString,
  cookie,
  savedConsent,
}) => {
  const initialEnabledNoticeKeys = () => {
    if (experience.privacy_notices) {
      // ensure we have most up-to-date cookie vals
      const parsedCookie: FidesCookie | undefined = getFidesConsentCookie();
      return experience.privacy_notices.map((notice) => {
        const val = resolveConsentValue(
          notice,
          getConsentContext(),
          parsedCookie?.consent
        );
        return val ? (notice.notice_key as PrivacyNotice["notice_key"]) : "";
      });
    }
    return [];
  };

  const [draftEnabledNoticeKeys, setDraftEnabledNoticeKeys] = useState<
    Array<PrivacyNotice["notice_key"]>
  >(initialEnabledNoticeKeys());

  const privacyNotices = useMemo(
    () => experience.privacy_notices ?? [],
    [experience.privacy_notices]
  );

  const isAllNoticeOnly = privacyNotices.every(
    (n) => n.consent_mechanism === ConsentMechanism.NOTICE_ONLY
  );

  const { servedNotice } = useConsentServed({
    notices: privacyNotices,
    options,
    userGeography: fidesRegionString,
    acknowledgeMode: isAllNoticeOnly,
    privacyExperience: experience,
  });

  const createConsentPreferencesToSave = (
    privacyNoticeList: PrivacyNotice[],
    enabledPrivacyNoticeKeys: string[]
  ): SaveConsentPreference[] =>
    privacyNoticeList.map((notice) => {
      const userPreference = transformConsentToFidesUserPreference(
        enabledPrivacyNoticeKeys.includes(notice.notice_key),
        notice.consent_mechanism
      );
      return new SaveConsentPreference(notice, userPreference);
    });

  const handleUpdatePreferences = useCallback(
    (
      consentMethod: ConsentMethod,
      enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>
    ) => {
      const consentPreferencesToSave = createConsentPreferencesToSave(
        privacyNotices,
        enabledPrivacyNoticeKeys
      );

      updateConsentPreferences({
        consentPreferencesToSave,
        experience,
        consentMethod,
        options,
        userLocationString: fidesRegionString,
        cookie,
        servedNoticeHistoryId: servedNotice?.served_notice_history_id,
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
      servedNotice,
    ]
  );

  const dispatchOpenBannerEvent = useCallback(() => {
    dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
      servingComponent: ServingComponent.BANNER,
    });
  }, [cookie, options.debug]);

  const dispatchOpenOverlayEvent = useCallback(() => {
    dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
      servingComponent: ServingComponent.MODAL,
    });
  }, [cookie, options.debug]);

  const handleDismiss = useCallback(() => {
    handleUpdatePreferences(ConsentMethod.DISMISS, initialEnabledNoticeKeys());
  }, [handleUpdatePreferences, initialEnabledNoticeKeys]);

  const experienceConfig = experience.experience_config;
  if (!experienceConfig) {
    debugLog(options.debug, "No experience config found");
    return null;
  }

  return (
    <Overlay
      options={options}
      experience={experience}
      i18n={i18n}
      cookie={cookie}
      savedConsent={savedConsent}
      onOpen={dispatchOpenOverlayEvent}
      onDismiss={handleDismiss}
      renderBanner={({ isOpen, onClose, onSave, onManagePreferencesClick }) => (
        <ConsentBanner
          bannerIsOpen={isOpen}
          onOpen={dispatchOpenBannerEvent}
          onClose={() => {
            onClose();
            handleDismiss();
          }}
          i18n={i18n}
          renderButtonGroup={({ isMobile }) => (
            <NoticeConsentButtons
              experience={experience}
              i18n={i18n}
              onManagePreferencesClick={onManagePreferencesClick}
              enabledKeys={draftEnabledNoticeKeys}
              onSave={(
                consentMethod: ConsentMethod,
                keys: Array<PrivacyNotice["notice_key"]>
              ) => {
                handleUpdatePreferences(consentMethod, keys);
                onSave();
              }}
              isAcknowledge={isAllNoticeOnly}
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
              i18n={i18n}
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
            i18n={i18n}
            enabledKeys={draftEnabledNoticeKeys}
            onSave={(
              consentMethod: ConsentMethod,
              keys: Array<PrivacyNotice["notice_key"]>
            ) => {
              handleUpdatePreferences(consentMethod, keys);
              onClose();
            }}
            isInModal
            isAcknowledge={isAllNoticeOnly}
            isMobile={isMobile}
            saveOnly={privacyNotices.length === 1}
          />
          <PrivacyPolicyLink i18n={i18n} />
        </Fragment>
      )}
    />
  );
};

export default NoticeOverlay;
