import "../fides.css";

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
} from "preact/hooks";

import { FidesEvent } from "../../docs/fides-event";
import { getConsentContext } from "../../lib/consent-context";
import {
  AssetType,
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
import {
  InitializedFidesGlobal,
  useFidesGlobal,
} from "../../lib/providers/fides-global-context";
import { processExternalConsentValue } from "../../lib/shared-consent-utils";
import ConsentBanner from "../ConsentBanner";
import { NoticeConsentButtons } from "../ConsentButtons";
import Overlay from "../Overlay";
import { NoticeToggleProps, NoticeToggles } from "./NoticeToggles";
import VendorAssetDisclosure from "./VendorAssetDisclosure";

const NoticeOverlay = () => {
  const { fidesGlobal, setFidesGlobal } = useFidesGlobal();
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

  const getEnabledNoticeKeys = useCallback(
    (consent: NoticeConsent) => {
      if (experience.privacy_notices) {
        // ensure we have most up-to-date cookie vals, including GPC and other automated consent applied during initialization
        return experience.privacy_notices.map((notice) => {
          const val = resolveConsentValue(notice, consent);
          return val ? (notice.notice_key as PrivacyNotice["notice_key"]) : "";
        });
      }
      return [];
    },
    [experience.privacy_notices],
  );

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
  >(getEnabledNoticeKeys(cookie?.consent));

  /**
   * If GPC is being applied after initialization, we need to update the initial overlay
   * to reflect the new state. This is especially important for Firefox browsers (Gecko)
   * because GPC gets applied rather late due to how it queues the `setTimeout` on the last
   * step of our `initialize` function.
   *
   * Effect is needed to avoid memory leaks and to allow cleanup.
   * Use `useLayoutEffect` instead of `useEffect` to ensure the listener is attached
   * as early as possible, before the browser paints. This prevents a race condition
   * where the FidesUpdating event (triggered by GPC) fires before the listener is ready.
   */
  useLayoutEffect(() => {
    const handleFidesUpdating = (event: Event) => {
      const fidesEvent = event as FidesEvent;
      const { consent } = fidesEvent.detail;
      Object.entries(consent).forEach(([key, value]) => {
        consent[key] = processExternalConsentValue(value);
      });
      setDraftEnabledNoticeKeys(getEnabledNoticeKeys(consent));

      // only need to run during initialization, no need to listen for subsequent updates
      window.removeEventListener("FidesUpdating", handleFidesUpdating);
    };

    window.addEventListener("FidesUpdating", handleFidesUpdating);

    return () => {
      window.removeEventListener("FidesUpdating", handleFidesUpdating);
    };
    // only need to run once on mount, no dependency watch needed
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      cookies: item.notice.cookies,
      checked,
      consentMechanism: item.notice.consent_mechanism,
      disabled: item.notice.disabled,
      gpcStatus,
    };
  });

  const [isVendorAssetDisclosureView, setIsVendorAssetDisclosureView] =
    useState(false);
  const [selectedNoticeKey, setSelectedNoticeKey] = useState<string | null>(
    null,
  );

  const selectedNotice = useMemo(() => {
    if (!selectedNoticeKey) {
      return null;
    }
    return privacyNoticeItems.find(
      (item) => item.notice.notice_key === selectedNoticeKey,
    );
  }, [selectedNoticeKey, privacyNoticeItems]);

  const noticesWithCookies = privacyNoticeItems
    .map((item) => ({
      noticeKey: item.notice.notice_key,
      title: item.bestTranslation?.title || item.notice.name || "",
      cookies: item.notice.cookies || [],
    }))
    .filter((n) => n.cookies && n.cookies.length > 0);
  const cookiesBySelectedNotice = selectedNoticeKey
    ? noticesWithCookies.filter((n) => n.noticeKey === selectedNoticeKey)
    : noticesWithCookies;

  useNoticesServed({
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
      updateConsent(fidesGlobal, {
        noticeConsent,
        consentMethod,
        eventExtraDetails: {
          servingComponent: servingComponentRef.current,
          trigger: triggerRef.current,
        },
      }).finally(() => {
        if (window.Fides) {
          // apply any updates to the fidesGlobal
          setFidesGlobal(window.Fides as InitializedFidesGlobal);
        }
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
      setTrigger,
      setFidesGlobal,
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
        getEnabledNoticeKeys(cookie?.consent),
      );
    }
  }, [
    handleUpdatePreferences,
    getEnabledNoticeKeys,
    parsedCookie?.consent,
    cookie?.consent,
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
      isVendorAssetDisclosureView={isVendorAssetDisclosureView}
      onModalHide={() => {
        setIsVendorAssetDisclosureView(false);
        setSelectedNoticeKey(null);
      }}
      headerContent={
        isVendorAssetDisclosureView && selectedNotice
          ? {
              title:
                selectedNotice.bestTranslation?.title ||
                selectedNotice.notice.name ||
                "",
              description: selectedNotice.bestTranslation?.description || "",
            }
          : undefined
      }
      onOpen={dispatchOpenOverlayEvent}
      onDismiss={handleDismiss}
      renderBanner={({
        attributes,
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
            attributes={attributes}
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
          {isVendorAssetDisclosureView ? (
            <VendorAssetDisclosure
              cookiesByNotice={cookiesBySelectedNotice}
              onBack={() => {
                setIsVendorAssetDisclosureView(false);
                setSelectedNoticeKey(null);
              }}
            />
          ) : (
            <div className="fides-modal-notices">
              <NoticeToggles
                noticeToggles={noticeToggles}
                enabledNoticeKeys={draftEnabledNoticeKeys}
                onChange={handleToggleChange}
                renderDescription={(props) => {
                  const hasCookies = (props.cookies || []).length > 0;
                  return (
                    <div>
                      {props.description}
                      {hasCookies &&
                      // only "Cookie" asset types are currently supported for vendor disclosure
                      experience.experience_config?.asset_disclosure_include_types?.includes(
                        AssetType.COOKIE,
                      ) &&
                      experience.experience_config
                        ?.allow_vendor_asset_disclosure ? (
                        <div style={{ marginTop: "12px" }}>
                          <button
                            type="button"
                            className="fides-link-button fides-vendors-disclosure-link"
                            onClick={() => {
                              setSelectedNoticeKey(props.noticeKey);
                              setIsVendorAssetDisclosureView(true);
                            }}
                          >
                            {i18n.t("static.other.vendors")}
                          </button>
                        </div>
                      ) : null}
                    </div>
                  );
                }}
              />
            </div>
          )}
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
