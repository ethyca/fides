import "../fides.css";

import { h } from "preact";
import { useCallback, useEffect, useMemo, useState } from "preact/hooks";

import { FidesEvent } from "../../docs/fides-event";
import { getConsentContext } from "../../lib/consent-context";
import {
  ConsentMechanism,
  ConsentMethod,
  FidesCookie,
  Layer1ButtonOption,
  NoticeConsent,
  PrivacyExperience,
  PrivacyNotice,
  PrivacyNoticeItem,
  ServingComponent,
} from "../../lib/consent-types";
import {
  getGpcStatusFromNotice,
  isConsentOverride,
} from "../../lib/consent-utils";
import { resolveConsentValue } from "../../lib/consent-value";
import {
  consentCookieObjHasSomeConsentSet,
  getFidesConsentCookie,
} from "../../lib/cookie";
import {
  FidesEventDetailsPreference,
  FidesEventDetailsServingComponent,
} from "../../lib/events";
import { useNoticesServed } from "../../lib/hooks";
import {
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
} from "../../lib/i18n";
import { useI18n } from "../../lib/i18n/i18n-context";
import { updateConsent } from "../../lib/preferences";
import { useEvent } from "../../lib/providers/event-context";
import { useFidesGlobal } from "../../lib/providers/fides-global-context";
import { processExternalConsentValue } from "../../lib/shared-consent-utils";
import ConsentBanner from "../ConsentBanner";
import { NoticeConsentButtons } from "../ConsentButtons";
import Overlay from "../Overlay";
import { NoticeToggleProps, NoticeToggles } from "./NoticeToggles";

const NoticeOverlay = () => {
  const { fidesGlobal } = useFidesGlobal();
  const {
    fidesRegionString,
    cookie,
    options,
    saved_consent: savedConsent,
  } = fidesGlobal;
  const experience = fidesGlobal.experience as PrivacyExperience;
  const { i18n, currentLocale, setCurrentLocale } = useI18n();
  const {
    triggerRef,
    setTrigger,
    servingComponentRef,
    setServingComponent,
    dispatchFidesEventAndClearTrigger,
  } = useEvent();
  const parsedCookie: FidesCookie | undefined = getFidesConsentCookie();

  // TODO (PROD-1792): restore useMemo here but ensure that saved changes are respected
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const initialEnabledNoticeKeys = (consent?: NoticeConsent) => {
    if (experience.privacy_notices) {
      // ensure we have most up-to-date cookie vals. If we don't have any consent, use the savedConsent which will be the default values that haven't been passed through the privacy_notices yet so it's perfect to use here.
      return experience.privacy_notices.map((notice) => {
        const val = resolveConsentValue(
          notice,
          consent || savedConsent || parsedCookie?.consent,
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
        currentLocale,
        i18n.getDefaultLocale(),
        experience.experience_config,
      );
      return bestTranslation?.privacy_experience_config_history_id;
    }
    return undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [experience, currentLocale]);

  /**
   * Collect the given PrivacyNotices into a list of "items" for rendering.
   *
   * Each "item" includes both:
   * 1) notice: The PrivacyNotice itself with it's properties like keys,
   *    preferences, etc. We also check if the notice needs to be disabled
   *    based on the fidesDisabledNotices option or if the notice is a
   *    notice-only notice.
   * 2) bestTranslation: The "best" translation for the notice based on the
   *    current locale
   *
   * We memoize these together to avoid repeatedly figuring out disabled status and the "best"
   * translation on every render.
   */
  const privacyNoticeItems: PrivacyNoticeItem[] = useMemo(
    () => {
      const privacyNotices = experience.privacy_notices ?? [];
      const items = privacyNotices.map((notice) => {
        const disabled =
          notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY ||
          (options.fidesDisabledNotices?.includes(notice.notice_key) ??
            false) ||
          notice.disabled;
        const bestTranslation = selectBestNoticeTranslation(
          currentLocale,
          i18n.getDefaultLocale(),
          notice,
        );
        return { notice: { ...notice, disabled }, bestTranslation };
      });

      const noticeOnly = items.filter(
        (item) =>
          item.notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY,
      );
      const others = items.filter(
        (item) =>
          item.notice.consent_mechanism !== ConsentMechanism.NOTICE_ONLY,
      );
      return [...noticeOnly, ...others];
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [experience.privacy_notices, currentLocale, options.fidesDisabledNotices],
  );

  const [draftEnabledNoticeKeys, setDraftEnabledNoticeKeys] = useState<
    Array<string>
  >(initialEnabledNoticeKeys());

  window.addEventListener("FidesUpdating", (event) => {
    // If GPC is being applied after initialization, we need to update the initial overlay to reflect the new state. This is especially important for Firefox browsers (Gecko) because GPC gets applied rather late due to how it handles queuing the `setTimeout` on the last step of our `initialize` function.
    const { consent } = event.detail;
    Object.entries(consent).forEach(([key, value]) => {
      consent[key] = processExternalConsentValue(value);
    });
    setDraftEnabledNoticeKeys(initialEnabledNoticeKeys(consent));
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
      disabled: item.notice.disabled,
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
  });

  const handleUpdatePreferences = useCallback(
    (
      consentMethod: ConsentMethod,
      enabledPrivacyNoticeKeys: Array<PrivacyNotice["notice_key"]>,
    ) => {
      const noticeConsent: NoticeConsent = {};
      privacyNoticeItems.forEach((item) => {
        if (item.notice.consent_mechanism !== ConsentMechanism.NOTICE_ONLY) {
          noticeConsent[item.notice.notice_key] =
            enabledPrivacyNoticeKeys.includes(item.notice.notice_key);
        } else {
          // always set notice-only notices to true
          noticeConsent[item.notice.notice_key] = true;
        }
      });
      updateConsent(
        fidesGlobal,
        {
          noticeConsent,
          consentMethod,
          eventExtraDetails: {
            servingComponent: servingComponentRef.current,
            trigger: triggerRef.current,
          },
        },
        servedNoticeHistoryId,
      ).finally(() => {
        setTrigger(undefined);
      });
      // Make sure our draft state also updates
      setDraftEnabledNoticeKeys(enabledPrivacyNoticeKeys);
    },
    [
      privacyNoticeItems,
      fidesGlobal,
      servingComponentRef,
      triggerRef,
      servedNoticeHistoryId,
      setTrigger,
    ],
  );

  const handleAcceptAll = useCallback(
    (wasAutomated?: boolean) => {
      handleUpdatePreferences(
        wasAutomated ? ConsentMethod.SCRIPT : ConsentMethod.ACCEPT,
        privacyNoticeItems
          .filter((n) => {
            return (
              !n.notice.disabled ||
              draftEnabledNoticeKeys.includes(n.notice.notice_key)
            );
          })
          .map((n) => n.notice.notice_key),
      );
    },
    [draftEnabledNoticeKeys, handleUpdatePreferences, privacyNoticeItems],
  );

  const handleRejectAll = useCallback(
    (wasAutomated?: boolean) => {
      handleUpdatePreferences(
        wasAutomated ? ConsentMethod.SCRIPT : ConsentMethod.REJECT,
        privacyNoticeItems
          .filter((n) => {
            return (
              n.notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY ||
              (n.notice.disabled &&
                draftEnabledNoticeKeys.includes(n.notice.notice_key))
            );
          })
          .map((n) => n.notice.notice_key),
      );
    },
    [draftEnabledNoticeKeys, handleUpdatePreferences, privacyNoticeItems],
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
    setServingComponent(ServingComponent.BANNER);
    dispatchFidesEventAndClearTrigger("FidesUIShown", cookie);
  }, [cookie, dispatchFidesEventAndClearTrigger, setServingComponent]);

  const dispatchOpenOverlayEvent = useCallback(
    (origin?: string) => {
      setServingComponent(ServingComponent.MODAL);
      dispatchFidesEventAndClearTrigger("FidesUIShown", cookie, {
        trigger: {
          origin,
        },
      });
    },
    [cookie, dispatchFidesEventAndClearTrigger, setServingComponent],
  );

  const handleDismiss = useCallback(() => {
    if (!consentCookieObjHasSomeConsentSet(parsedCookie?.consent)) {
      handleUpdatePreferences(
        ConsentMethod.DISMISS,
        initialEnabledNoticeKeys(),
      );
    }
  }, [
    handleUpdatePreferences,
    initialEnabledNoticeKeys,
    parsedCookie?.consent,
  ]);

  const handleToggleChange = useCallback(
    (updatedKeys: Array<string>, preference: FidesEventDetailsPreference) => {
      const eventExtraDetails: FidesEvent["detail"]["extraDetails"] = {
        servingComponent:
          servingComponentRef.current as FidesEventDetailsServingComponent,
        trigger: triggerRef.current,
        preference,
      };
      setDraftEnabledNoticeKeys(updatedKeys);
      dispatchFidesEventAndClearTrigger(
        "FidesUIChanged",
        cookie,
        eventExtraDetails,
      );
    },
    [
      triggerRef,
      dispatchFidesEventAndClearTrigger,
      cookie,
      servingComponentRef,
    ],
  );

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
              onChange={handleToggleChange}
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
