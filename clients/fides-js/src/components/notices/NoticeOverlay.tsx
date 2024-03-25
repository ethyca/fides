import "../fides.css";

import { Fragment, FunctionComponent, h } from "preact";
import { useCallback, useMemo, useState } from "preact/hooks";

import { getConsentContext } from "../../lib/consent-context";
import {
  ConsentMechanism,
  ConsentMethod,
  FidesCookie,
  PrivacyNotice,
  PrivacyNoticeTranslation,
  PrivacyNoticeWithPreference,
  SaveConsentPreference,
  ServingComponent,
} from "../../lib/consent-types";
import { debugLog, getGpcStatusFromNotice } from "../../lib/consent-utils";
import { resolveConsentValue } from "../../lib/consent-value";
import {
  getFidesConsentCookie,
  updateCookieFromNoticePreferences,
} from "../../lib/cookie";
import { dispatchFidesEvent } from "../../lib/events";
import { useConsentServed } from "../../lib/hooks";
import {
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
} from "../../lib/i18n";
import { updateConsentPreferences } from "../../lib/preferences";
import { transformConsentToFidesUserPreference } from "../../lib/shared-consent-utils";
import ConsentBanner from "../ConsentBanner";
import { NoticeConsentButtons } from "../ConsentButtons";
import Overlay from "../Overlay";
import PrivacyPolicyLink from "../PrivacyPolicyLink";
import { OverlayProps } from "../types";
import { NoticeToggleProps, NoticeToggles } from "./NoticeToggles";
import { useI18n } from "../../lib/i18n/i18n-context";

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
  savedConsent,
}) => {
  // TODO (PROD-1792): restore useMemo here but ensure that saved changes are respected
  const initialEnabledNoticeKeys = () => {
    if (experience.privacy_notices) {
      // ensure we have most up-to-date cookie vals
      // TODO (PROD-1792): we should be able to replace parsedCookie with savedConsent
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

  const { currentLocale } = useI18n();

  /**
   * Determine which ExperienceConfig translation is being used based on the
   * current locale and memo-ize it's history ID to use for all API calls
   */
  const privacyExperienceConfigHistoryId: string | undefined = useMemo(() => {
    if (experience.experience_config && currentLocale) {
      const bestTranslation = selectBestExperienceConfigTranslation(
        i18n,
        experience.experience_config
      );
      return bestTranslation?.privacy_experience_config_history_id;
    }
    return undefined;
  }, [experience, i18n, currentLocale]);

  /**
   * Collect the given PrivacyNotices into a list of "items" for rendering.
   *
   * Each "item" includes both:
   * 1) notice: The PrivacyNotice itself with it's properties like keys,
   *    preferences, etc.
   * 2) bestTranslation: The "best" translation for the notice based on the
   *    current locale
   *
   * We memoize these together to avoid repeatedly figuring out the "best"
   * translation on every render, since it will only change if the overall
   * locale changes!
   */
  const privacyNoticeItems: PrivacyNoticeItem[] = useMemo(
    () =>
      (experience.privacy_notices || []).map((notice) => {
        const bestTranslation = selectBestNoticeTranslation(i18n, notice);
        return { notice, bestTranslation };
      }),
    [experience.privacy_notices, i18n]
  );

  const [draftEnabledNoticeKeys, setDraftEnabledNoticeKeys] = useState<
    Array<string>
  >(initialEnabledNoticeKeys());

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

  const { servedNotice } = useConsentServed({
    privacyExperienceConfigHistoryId,
    privacyNoticeHistoryIds: privacyNoticeItems.reduce((ids, e) => {
      const id = e.bestTranslation?.privacy_notice_history_id;
      if (id) {
        ids.push(id);
      }
      return ids;
    }, [] as string[]),
    options,
    userGeography: fidesRegionString,
    acknowledgeMode: isAllNoticeOnly,
    privacyExperience: experience,
  });

  const createConsentPreferencesToSave = (
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
        privacyExperienceConfigHistoryId,
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
      cookie,
      fidesRegionString,
      experience,
      options,
      privacyExperienceConfigHistoryId,
      privacyNoticeItems,
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
          dismissable={experience.experience_config?.dismissable}
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
              fidesPreviewMode={options.fidesPreviewMode}
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
                if (options.fidesPreviewMode) {
                  return;
                }
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
            fidesPreviewMode={options.fidesPreviewMode}
          />
          <PrivacyPolicyLink i18n={i18n} />
        </Fragment>
      )}
    />
  );
};

export default NoticeOverlay;
