import { h, Fragment, FunctionComponent } from "preact";
import { useCallback, useMemo, useState } from "preact/hooks";
// TODO (PROD-1597): sort out all these imports!
import {
  ConsentMechanism,
  ConsentMethod,
  PrivacyNotice,
  PrivacyNoticeTranslation,
  PrivacyNoticeWithPreference,
  SaveConsentPreference,
  ServingComponent,
} from "../../lib/consent-types";
import ConsentBanner from "../ConsentBanner";

import { updateConsentPreferences } from "../../lib/preferences";
import { debugLog, getGpcStatusFromNotice } from "../../lib/consent-utils";

import "../fides.css";
import Overlay from "../Overlay";
import { NoticeConsentButtons } from "../ConsentButtons";
import { NoticeToggles, NoticeToggleProps } from "./NoticeToggles";
import { OverlayProps } from "../types";
import { useConsentServed } from "../../lib/hooks";
import { updateCookieFromNoticePreferences } from "../../lib/cookie";
import PrivacyPolicyLink from "../PrivacyPolicyLink";
import { dispatchFidesEvent } from "../../lib/events";
import { resolveConsentValue } from "../../lib/consent-value";
import { getConsentContext } from "../../lib/consent-context";
import { transformConsentToFidesUserPreference } from "../../lib/shared-consent-utils";
import { selectBestNoticeTranslation } from "../../lib/i18n";

/**
 * Define a special PrivacyNoticeItem, where we've narrowed the list of
 * available translations to the singular "best" translation that should be
 * displayed, and paired that with the source notice itself.
 */
type PrivacyNoticeItem = {
  notice: PrivacyNoticeWithPreference;
  bestTranslation: PrivacyNoticeTranslation | null;
};

const NoticeOverlay: FunctionComponent<OverlayProps> = ({
  options,
  experience,
  i18n,
  fidesRegionString,
  cookie,
}) => {
  const initialEnabledNoticeKeys = useMemo(() => {
    if (experience.privacy_notices) {
      return experience.privacy_notices.map((notice) => {
        const val = resolveConsentValue(notice, getConsentContext(), cookie);
        return val ? (notice.notice_key as PrivacyNotice["notice_key"]) : "";
      });
    }
    return [];
  }, [cookie, experience]);

  const [draftEnabledNoticeKeys, setDraftEnabledNoticeKeys] = useState<
    Array<PrivacyNotice["notice_key"]>
  >(initialEnabledNoticeKeys);

  // TODO: comment
  const privacyNoticeItems: PrivacyNoticeItem[] = useMemo(
    () =>
      (experience.privacy_notices || []).map((notice) => {
        const bestTranslation = selectBestNoticeTranslation(i18n, notice);
        return { notice, bestTranslation };
      }),
    [experience.privacy_notices, i18n]
  );

  const isAllNoticeOnly = privacyNoticeItems.every(
    (n) => n.notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY
  );

  // Calculate the "notice toggles" props for display based on the current state
  const noticeToggles: NoticeToggleProps[] = privacyNoticeItems.map((item) => {
    const checked =
      draftEnabledNoticeKeys.indexOf(item.notice.notice_key) !== -1;
    const consentContext = getConsentContext();
    const gpcStatus = getGpcStatusFromNotice({
      value: checked,
      notice: item.notice,
      consentContext,
    });

    return {
      noticeKey: item.notice.notice_key,
      title: item.bestTranslation?.title,
      description: item.bestTranslation?.description,
      checked,
      consentMechanism: item.notice.consent_mechanism,
      disabled: item.notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY,
      gpcStatus,
    };
  });

  // TODO: use translations correctly
  const { servedNotice } = useConsentServed({
    privacyExperienceConfigHistoryId:
      experience.experience_config?.translations[0]
        .privacy_experience_config_history_id,
    privacyNoticeHistoryIds: privacyNoticeItems.map(
      (e) => e.bestTranslation?.privacy_notice_history_id
    ),
    options,
    userGeography: fidesRegionString,
    acknowledgeMode: isAllNoticeOnly,
    privacyExperience: experience,
  });

  const createConsentPreferencesToSave = (
    // TODO: remove use of the notices, only use translated toggle props
    privacyNoticeList: PrivacyNoticeItem[],
    enabledPrivacyNoticeKeys: string[]
  ): SaveConsentPreference[] =>
    privacyNoticeList.map((item) => {
      const userPreference = transformConsentToFidesUserPreference(
        enabledPrivacyNoticeKeys.includes(item.notice.notice_key),
        item.notice.consent_mechanism
      );
      return new SaveConsentPreference(
        item.notice,
        userPreference,
        item.bestTranslation?.privacy_notice_history_id
      );
    });

  const handleUpdatePreferences = useCallback(
    (
      consentMethod: ConsentMethod,
      enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>
    ) => {
      const consentPreferencesToSave = createConsentPreferencesToSave(
        privacyNoticeItems,
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
      privacyNoticeItems,
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
    handleUpdatePreferences(ConsentMethod.DISMISS, initialEnabledNoticeKeys);
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
              noticeToggles={noticeToggles}
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
            saveOnly={privacyNoticeItems.length === 1}
          />
          <PrivacyPolicyLink i18n={i18n} />
        </Fragment>
      )}
    />
  );
};

export default NoticeOverlay;
