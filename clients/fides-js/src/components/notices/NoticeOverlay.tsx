import "../fides.css";

import { FunctionComponent, h } from "preact";
import { useCallback, useEffect, useMemo, useState } from "preact/hooks";

import { isConsentOverride } from "../../lib/common-utils";
import { getConsentContext } from "../../lib/consent-context";
import {
  ConsentMechanism,
  ConsentMethod,
  FidesCookie,
  Layer1ButtonOption,
  NoticeConsent,
  PrivacyNotice,
  PrivacyNoticeTranslation,
  PrivacyNoticeWithPreference,
  SaveConsentPreference,
  ServingComponent,
} from "../../lib/consent-types";
import { getGpcStatusFromNotice } from "../../lib/consent-utils";
import { resolveConsentValue } from "../../lib/consent-value";
import {
  getFidesConsentCookie,
  updateCookieFromNoticePreferences,
} from "../../lib/cookie";
import { dispatchFidesEvent } from "../../lib/events";
import { useNoticesServed } from "../../lib/hooks";
import {
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
} from "../../lib/i18n";
import { useI18n } from "../../lib/i18n/i18n-context";
import { updateConsentPreferences } from "../../lib/preferences";
import { transformConsentToFidesUserPreference } from "../../lib/shared-consent-utils";
import ConsentBanner from "../ConsentBanner";
import { NoticeConsentButtons } from "../ConsentButtons";
import Overlay from "../Overlay";
import { OverlayProps } from "../types";
import { NoticeToggleProps, NoticeToggles } from "./NoticeToggles";

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
  fidesRegionString,
  cookie,
  savedConsent,
  propertyId,
}) => {
  const { i18n, currentLocale, setCurrentLocale } = useI18n();

  // TODO (PROD-1792): restore useMemo here but ensure that saved changes are respected
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const initialEnabledNoticeKeys = (consent?: NoticeConsent) => {
    if (experience.privacy_notices) {
      // ensure we have most up-to-date cookie vals
      return experience.privacy_notices.map((notice) => {
        const val = resolveConsentValue(
          notice,
          getConsentContext(),
          consent || savedConsent,
        );
        return val ? (notice.notice_key as PrivacyNotice["notice_key"]) : "";
      });
    }
    return [];
  };

  useEffect(() => {
    if (!currentLocale && i18n.locale) {
      setCurrentLocale(i18n.locale);
    }
  }, [currentLocale, i18n.locale, setCurrentLocale]);

  /**
   * Determine which ExperienceConfig translation is being used based on the
   * current locale and memo-ize it's history ID to use for all API calls
   */
  const privacyExperienceConfigHistoryId: string | undefined = useMemo(() => {
    if (experience.experience_config) {
      const bestTranslation = selectBestExperienceConfigTranslation(
        i18n,
        experience.experience_config,
      );
      return bestTranslation?.privacy_experience_config_history_id;
    }
    return undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [experience.privacy_notices, i18n, currentLocale],
  );

  const [draftEnabledNoticeKeys, setDraftEnabledNoticeKeys] = useState<
    Array<string>
  >(initialEnabledNoticeKeys());

  window.addEventListener("FidesUpdating", (event) => {
    // If GPC is being applied after initialization, we need to update the initial overlay to reflect the new state. This is especially important for Firefox browsers (Gecko) because GPC gets applied rather late due to how it handles queuing the `setTimeout` on the last step of our `initialize` function.
    setDraftEnabledNoticeKeys(initialEnabledNoticeKeys(event.detail.consent));
  });

  const isAllNoticeOnly = privacyNoticeItems.every(
    (n) => n.notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY,
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
      title: item.bestTranslation?.title || item.notice.name || "",
      description: item.bestTranslation?.description,
      checked,
      consentMechanism: item.notice.consent_mechanism,
      disabled: item.notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY,
      gpcStatus,
    };
  });

  const { servedNoticeHistoryId } = useNoticesServed({
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
    propertyId,
  });

  const createConsentPreferencesToSave = (
    privacyNoticeList: PrivacyNoticeItem[],
    enabledPrivacyNoticeKeys: string[],
  ): SaveConsentPreference[] =>
    privacyNoticeList.map((item) => {
      const userPreference = transformConsentToFidesUserPreference(
        enabledPrivacyNoticeKeys.includes(item.notice.notice_key),
        item.notice.consent_mechanism,
      );
      return new SaveConsentPreference(
        item.notice,
        userPreference,
        item.bestTranslation?.privacy_notice_history_id,
      );
    });

  const handleUpdatePreferences = useCallback(
    (
      consentMethod: ConsentMethod,
      enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>,
    ) => {
      const consentPreferencesToSave = createConsentPreferencesToSave(
        privacyNoticeItems,
        enabledPrivacyNoticeKeys,
      );

      updateConsentPreferences({
        consentPreferencesToSave,
        privacyExperienceConfigHistoryId,
        experience,
        consentMethod,
        options,
        userLocationString: fidesRegionString,
        cookie,
        servedNoticeHistoryId,
        propertyId,
        updateCookie: (oldCookie) =>
          updateCookieFromNoticePreferences(
            oldCookie,
            consentPreferencesToSave,
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
      servedNoticeHistoryId,
      propertyId,
    ],
  );

  const handleAcceptAll = useCallback(
    (wasAutomated?: boolean) => {
      handleUpdatePreferences(
        wasAutomated ? ConsentMethod.SCRIPT : ConsentMethod.ACCEPT,
        privacyNoticeItems.map((n) => n.notice.notice_key),
      );
    },
    [handleUpdatePreferences, privacyNoticeItems],
  );

  const handleRejectAll = useCallback(
    (wasAutomated?: boolean) => {
      handleUpdatePreferences(
        wasAutomated ? ConsentMethod.SCRIPT : ConsentMethod.REJECT,
        privacyNoticeItems
          .filter(
            (n) => n.notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY,
          )
          .map((n) => n.notice.notice_key),
      );
    },
    [handleUpdatePreferences, privacyNoticeItems],
  );

  useEffect(() => {
    if (isConsentOverride(options) && experience.privacy_notices) {
      if (options.fidesConsentOverride === ConsentMethod.ACCEPT) {
        fidesDebugger(
          "Consent automatically accepted by fides_consent_override!",
        );
        handleAcceptAll(true);
      } else if (options.fidesConsentOverride === ConsentMethod.REJECT) {
        fidesDebugger(
          "Consent automatically rejected by fides_consent_override!",
        );
        handleRejectAll(true);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [experience.privacy_notices, options.fidesConsentOverride]);

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
    fidesDebugger("No experience config found");
    return null;
  }

  const isDismissable = !!experience.experience_config?.dismissable;

  const isSaveOnly = privacyNoticeItems.length === 1;

  return (
    <Overlay
      options={options}
      experience={experience}
      cookie={cookie}
      savedConsent={savedConsent}
      isUiBlocking={!isDismissable}
      onOpen={dispatchOpenOverlayEvent}
      onDismiss={handleDismiss}
      renderBanner={({
        isEmbedded,
        isOpen,
        onClose,
        onManagePreferencesClick,
      }) => {
        const isAcknowledge =
          isAllNoticeOnly ||
          experience.experience_config?.layer1_button_options ===
            Layer1ButtonOption.ACKNOWLEDGE;
        return (
          <ConsentBanner
            bannerIsOpen={isOpen}
            dismissable={isDismissable}
            onOpen={dispatchOpenBannerEvent}
            onClose={() => {
              onClose();
              handleDismiss();
            }}
            isEmbedded={isEmbedded}
            renderButtonGroup={() => (
              <NoticeConsentButtons
                experience={experience}
                onManagePreferencesClick={onManagePreferencesClick}
                enabledKeys={draftEnabledNoticeKeys}
                onAcceptAll={() => {
                  handleAcceptAll();
                  onClose();
                }}
                onRejectAll={() => {
                  handleRejectAll();
                  onClose();
                }}
                onSave={(
                  consentMethod: ConsentMethod,
                  keys: Array<PrivacyNotice["notice_key"]>,
                ) => {
                  handleUpdatePreferences(consentMethod, keys);
                  onClose();
                }}
                isAcknowledge={isAcknowledge}
                hideOptInOut={isAcknowledge}
                options={options}
              />
            )}
          />
        );
      }}
      renderModalContent={() => (
        <div>
          <div className="fides-modal-notices">
            <NoticeToggles
              noticeToggles={noticeToggles}
              enabledNoticeKeys={draftEnabledNoticeKeys}
              onChange={(updatedKeys) => {
                setDraftEnabledNoticeKeys(updatedKeys);
                dispatchFidesEvent("FidesUIChanged", cookie, options.debug);
              }}
            />
          </div>
        </div>
      )}
      renderModalFooter={({ onClose }) => (
        <NoticeConsentButtons
          experience={experience}
          enabledKeys={draftEnabledNoticeKeys}
          onAcceptAll={() => {
            handleAcceptAll();
            onClose();
          }}
          onRejectAll={() => {
            handleRejectAll();
            onClose();
          }}
          onSave={(
            consentMethod: ConsentMethod,
            keys: Array<PrivacyNotice["notice_key"]>,
          ) => {
            handleUpdatePreferences(consentMethod, keys);
            onClose();
          }}
          isInModal
          isAcknowledge={isAllNoticeOnly}
          hideOptInOut={isSaveOnly || isAllNoticeOnly}
          options={options}
        />
      )}
    />
  );
};

export default NoticeOverlay;
