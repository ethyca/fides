import "../fides.css";
import "./fides-tcf.css";

import { useCallback, useEffect, useMemo, useState } from "preact/hooks";

import { FidesEvent } from "../../docs/fides-event";
import {
  ButtonType,
  ConsentMechanism,
  ConsentMethod,
  EmptyExperience,
  FidesCookie,
  FidesExperienceTranslationOverrides,
  FidesModalDefaultView,
  NoticeConsent,
  OverrideType,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  PrivacyNoticeWithPreference,
  RejectAllMechanism,
  ServingComponent,
} from "../../lib/consent-types";
import {
  experienceIsValid,
  isPrivacyExperience,
} from "../../lib/consent-utils";
import {
  consentCookieObjHasSomeConsentSet,
  getFidesConsentCookie,
} from "../../lib/cookie";
import {
  dispatchFidesEvent,
  FidesEventDetailsPreference,
  FidesEventDetailsServingComponent,
  FidesEventTargetType,
} from "../../lib/events";
import {
  FetchState,
  useAutoResetFlag,
  useNoticesServed,
  useRetryableFetch,
} from "../../lib/hooks";
import {
  DEFAULT_LOCALE,
  detectUserLocale,
  loadGVLMessagesFromExperience,
  loadMessagesFromExperience,
  loadMessagesFromGVLTranslations,
  matchAvailableLocales,
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
} from "../../lib/i18n";
import { useI18n } from "../../lib/i18n/i18n-context";
import { getOverridesByType } from "../../lib/initialize";
import { updateConsent } from "../../lib/preferences";
import { useEvent } from "../../lib/providers/event-context";
import {
  InitializedFidesGlobal,
  useFidesGlobal,
} from "../../lib/providers/fides-global-context";
import { EMPTY_ENABLED_IDS } from "../../lib/tcf/constants";
import { useGvl } from "../../lib/tcf/gvl-context";
import {
  EnabledIds,
  PrivacyNoticeWithBestTranslation,
  TcfModels,
  TcfSavePreferences,
} from "../../lib/tcf/types";
import {
  buildTcfEntitiesFromCookieAndFidesString as buildUserPrefs,
  constructTCFNoticesServedProps,
  createTcfSavePayload,
  createTcfSavePayloadFromMinExp,
  getEnabledIds,
  getEnabledIdsNotice,
  getGVLPurposeList,
  updateTCFCookie,
} from "../../lib/tcf/utils";
import { useVendorButton } from "../../lib/tcf/vendor-button-context";
import { fetchExperience, fetchGvlTranslations } from "../../services/api";
import Button from "../Button";
import ConsentBanner from "../ConsentBanner";
import Overlay from "../Overlay";
import { TCFBannerSupplemental } from "./TCFBannerSupplemental";
import { TcfConsentButtons } from "./TcfConsentButtons";
import TcfTabs from "./TcfTabs";

const getAllIds = (
  modelList: TcfModels | Array<PrivacyNoticeWithPreference>,
) => {
  if (!modelList) {
    return [];
  }
  return modelList.map((m) => `${m.id}`);
};

// gets the index of the tab to show by default based on the fidesModalDefaultView option
const parseModalDefaultView = (
  defaultView: FidesModalDefaultView = FidesModalDefaultView.PURPOSES,
): number => {
  const tabRoutes = [
    FidesModalDefaultView.PURPOSES,
    FidesModalDefaultView.FEATURES,
    FidesModalDefaultView.VENDORS,
  ];
  return tabRoutes.indexOf(defaultView);
};

export const TcfOverlay = () => {
  const { isActive: isSaved, activate: markSaved } = useAutoResetFlag(false);
  const { fidesGlobal, setFidesGlobal } = useFidesGlobal();
  const {
    fidesRegionString,
    cookie,
    config,
    options,
    saved_consent: savedConsent,
  } = fidesGlobal;
  const experienceMinimal = fidesGlobal.experience as PrivacyExperienceMinimal;
  const translationOverrides: Partial<FidesExperienceTranslationOverrides> =
    getOverridesByType<Partial<FidesExperienceTranslationOverrides>>(
      OverrideType.EXPERIENCE_TRANSLATION,
      config,
    );
  const {
    i18n,
    currentLocale,
    setCurrentLocale,
    setIsLoading: setIsI18nLoading,
  } = useI18n();
  const {
    triggerRef,
    setTrigger,
    servingComponentRef,
    setServingComponent,
    dispatchFidesEventAndClearTrigger,
  } = useEvent();
  const parsedCookie: FidesCookie | undefined = getFidesConsentCookie();
  const minExperienceLocale =
    experienceMinimal?.experience_config?.translations?.[0]?.language;
  const userlocale = detectUserLocale(
    navigator,
    options.fidesLocale,
    i18n.getDefaultLocale(),
  );
  const bestLocale = matchAvailableLocales(
    userlocale,
    experienceMinimal.available_locales || [],
    i18n.getDefaultLocale(),
  );

  useEffect(() => {
    if (!currentLocale) {
      // initialize the i18n locale using the minimal experience
      setCurrentLocale(minExperienceLocale);
    }
  }, [currentLocale, minExperienceLocale, setCurrentLocale]);

  const { gvlTranslations, setGvlTranslations } = useGvl();
  const [isGVLLangLoading, setIsGVLLangLoading] = useState(false);
  const loadGVLTranslations = async (locale: string) => {
    const gvlTranslationObjects = await fetchGvlTranslations(
      options.fidesApiUrl,
      [locale],
    );
    if (gvlTranslationObjects) {
      setGvlTranslations(gvlTranslationObjects[locale]);
      loadMessagesFromGVLTranslations(i18n, gvlTranslationObjects, [locale]);
      fidesDebugger(`Fides GVL translations loaded for ${locale}`);
    }
  };

  /**
   * Enhance the given PrivacyNotices with best translation for rendering.
   *
   * We memoize these together to avoid repeatedly figuring out the "best"
   * translation on every render, since it will only change if the overall
   * locale changes!
   */
  const privacyNoticesWithBestTranslation: PrivacyNoticeWithBestTranslation[] =
    useMemo(
      () =>
        (experienceMinimal.privacy_notices || []).map((notice) => {
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
          return { ...notice, bestTranslation, disabled };
        }),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [experienceMinimal.privacy_notices, currentLocale],
    );

  /**
   * TCF overlay loads with a minimal experience, which is then replaced with the full.
   * We do this to ensure the overlay can be rendered as quickly as possible.
   * The full experience is fetched after the component mounts, so we store it
   * in state to trigger a re-render when it arrives.
   */
  const [experienceFull, setExperienceFull] = useState<PrivacyExperience>();

  const { fetchState: fullExperienceState } = useRetryableFetch<
    PrivacyExperience | EmptyExperience
  >({
    fetcher: () =>
      fetchExperience({
        userLocationString: fidesRegionString,
        fidesApiUrl: options.fidesApiUrl,
        apiOptions: options.apiOptions,
        propertyId: experienceMinimal.property_id,
        requestMinimalTCF: false,
      }),
    validator: (result) =>
      isPrivacyExperience(result) &&
      Object.keys(result).length > 0 &&
      experienceIsValid(result),
    onSuccess: (result) => {
      if (isPrivacyExperience(result)) {
        // include user preferences from the cookie
        const userPrefs = buildUserPrefs(result, cookie);
        const fullExperience: PrivacyExperience = {
          ...result,
          ...userPrefs,
        };
        fullExperience.minimal_tcf = false;
        window.Fides.experience = {
          ...window.Fides.experience,
          ...fullExperience,
        };
        setFidesGlobal(window.Fides as InitializedFidesGlobal);
        setExperienceFull(fullExperience);
      }
    },
  });

  useEffect(() => {
    if (!!userlocale && bestLocale !== minExperienceLocale) {
      // The minimal experience translation is different from the user's language.
      // This occurs when the customer has set their overrides on the window object
      // which isn't available to us until the experience is fetched or when the
      // browser has cached the experience from a previous userLocale. In these cases,
      // we'll get the translations for the banner from the full experience.
      fidesDebugger(
        `Best locale does not match minimal experience locale (${minExperienceLocale})\nLoading translations from full experience = ${bestLocale}`,
      );
      setIsI18nLoading(true);
    }
    if (!!userlocale && bestLocale !== DEFAULT_LOCALE) {
      // We can only get English GVL translations from the experience.
      // If the user's locale is not English, we need to load them from the api.
      // This only affects the modal.
      setIsGVLLangLoading(true);
      loadGVLTranslations(bestLocale).then(() => {
        setIsGVLLangLoading(false);
      });
    }
    fidesDebugger("Fetching full TCF experience...");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const { setVendorCount } = useVendorButton();

  const [draftIds, setDraftIds] = useState<EnabledIds>(EMPTY_ENABLED_IDS);

  useEffect(() => {
    const isFullExperience = !!experienceFull;
    if (isFullExperience) {
      // Load messages from experience
      // This includes any custom notices, but not the GVL translations.
      loadMessagesFromExperience(i18n, experienceFull, translationOverrides);

      // Set the locale to the best locale
      setCurrentLocale(bestLocale);

      const shouldUseEnglish = bestLocale === DEFAULT_LOCALE;
      if (shouldUseEnglish) {
        // English (default) GVL translations are already included in the full experience,
        // so we can directly load them from the
        loadGVLMessagesFromExperience(i18n, experienceFull);
        setIsI18nLoading(false);
      }
      if (!shouldUseEnglish && !isGVLLangLoading) {
        setIsI18nLoading(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [experienceFull]);

  useEffect(() => {
    if (!experienceFull) {
      const defaultIds = EMPTY_ENABLED_IDS;
      if (experienceMinimal?.privacy_notices) {
        defaultIds.customPurposesConsent = getEnabledIdsNotice(
          experienceMinimal.privacy_notices,
        );
      }
      setDraftIds(defaultIds);
    } else {
      const {
        tcf_purpose_consents: consentPurposes = [],
        privacy_notices: customPurposes = [],
        tcf_purpose_legitimate_interests: legintPurposes = [],
        tcf_special_purposes: specialPurposes = [],
        tcf_features: features = [],
        tcf_special_features: specialFeatures = [],
        tcf_vendor_consents: consentVendors = [],
        tcf_vendor_legitimate_interests: legintVendors = [],
        tcf_system_consents: consentSystems = [],
        tcf_system_legitimate_interests: legintSystems = [],
      } = experienceFull as PrivacyExperience;

      // Vendors and systems are the same to the FE, so we combine them here
      setDraftIds({
        purposesConsent: getEnabledIds(consentPurposes),
        customPurposesConsent: getEnabledIdsNotice(customPurposes),
        purposesLegint: getEnabledIds(legintPurposes),
        specialPurposes: getEnabledIds(specialPurposes),
        features: getEnabledIds(features),
        specialFeatures: getEnabledIds(specialFeatures),
        vendorsConsent: getEnabledIds([...consentVendors, ...consentSystems]),
        vendorsLegint: getEnabledIds([...legintVendors, ...legintSystems]),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [experienceFull, experienceMinimal]);

  useEffect(() => {
    if (experienceMinimal.vendor_count && setVendorCount) {
      setVendorCount(experienceMinimal.vendor_count);
    }
  }, [experienceMinimal, setVendorCount]);

  // Determine which ExperienceConfig history ID should be used for the
  // reporting APIs, based on the selected locale
  const privacyExperienceConfigHistoryId: string | undefined = useMemo(() => {
    const experienceConfig =
      experienceFull?.experience_config || experienceMinimal.experience_config;
    if (experienceConfig) {
      const bestTranslation = selectBestExperienceConfigTranslation(
        currentLocale,
        i18n.getDefaultLocale(),
        experienceConfig,
      );
      return bestTranslation?.privacy_experience_config_history_id;
    }
    return undefined;
  }, [experienceMinimal, experienceFull, currentLocale, i18n]);

  const customPurposes: (string | undefined)[] = useMemo(() => {
    const notices = privacyNoticesWithBestTranslation.map(
      (notice) => notice.bestTranslation?.title || notice.name,
    );
    return notices;
  }, [privacyNoticesWithBestTranslation]);

  const purposes: string[] = useMemo(() => {
    if (gvlTranslations) {
      return getGVLPurposeList(gvlTranslations);
    }

    // Use full experience if available and the current locale is English
    if (experienceFull && currentLocale === DEFAULT_LOCALE) {
      const fullPurposeNames =
        experienceFull.tcf_purpose_consents?.map((p) => p.name) || [];
      const fullSpecialFeatureNames =
        experienceFull.tcf_special_features?.map((sf) => sf.name) || [];
      return [...fullPurposeNames, ...fullSpecialFeatureNames];
    }

    // Otherwise, use the minimal experience
    const tcfPurposeNames = experienceMinimal?.tcf_purpose_names || [];
    const tcfSpecialFeatureNames =
      experienceMinimal?.tcf_special_feature_names || [];
    return [...tcfPurposeNames, ...tcfSpecialFeatureNames];
  }, [experienceMinimal, experienceFull, gvlTranslations, currentLocale]);

  const tcfNoticesServed = constructTCFNoticesServedProps(
    experienceFull || experienceMinimal,
  );

  useNoticesServed({
    privacyExperienceConfigHistoryId,
    privacyNoticeHistoryIds: privacyNoticesWithBestTranslation.reduce(
      (ids, e) => {
        const id = e.bestTranslation?.privacy_notice_history_id;
        if (id) {
          ids.push(id);
        }
        return ids;
      },
      [] as string[],
    ),
    options,
    userGeography: fidesRegionString,
    acknowledgeMode: false,
    privacyExperience: experienceFull || experienceMinimal,
    tcfNoticesServed,
  });

  const handleUpdateAllPreferences = useCallback(
    (consentMethod: ConsentMethod, enabledIds: EnabledIds) => {
      if (!experienceFull && !experienceMinimal) {
        return;
      }
      let tcf: TcfSavePreferences;
      if (!experienceFull && experienceMinimal?.minimal_tcf) {
        tcf = createTcfSavePayloadFromMinExp({
          experience: experienceMinimal,
          enabledIds,
        });
      } else {
        tcf = createTcfSavePayload({
          experience: experienceFull as PrivacyExperience,
          enabledIds,
        });
      }

      const customPurposesConsent: NoticeConsent = {};
      privacyNoticesWithBestTranslation.forEach((notice) => {
        if (notice.consent_mechanism !== ConsentMechanism.NOTICE_ONLY) {
          customPurposesConsent[notice.notice_key] =
            enabledIds.customPurposesConsent.includes(notice.id);
        } else {
          // always set notice-only notices to true
          customPurposesConsent[notice.notice_key] = true;
        }
      });
      updateConsent(fidesGlobal, {
        noticeConsent: customPurposesConsent,
        consentMethod,
        eventExtraDetails: {
          servingComponent: servingComponentRef.current,
          trigger: triggerRef.current,
        },
        tcf,
        updateCookie: (oldCookie) => {
          return updateTCFCookie(
            oldCookie,
            tcf,
            enabledIds,
            experienceFull || experienceMinimal,
            customPurposesConsent,
            (result) => {
              if (experienceFull) {
                const updatedTcfEntities = buildUserPrefs(
                  experienceFull,
                  result,
                );
                // update the experienceFull state with the new user preferences from the updated cookie
                setExperienceFull({
                  ...experienceFull,
                  ...updatedTcfEntities,
                });
              }
            },
          );
        },
      }).finally(() => {
        if (window.Fides) {
          // apply any updates to the fidesGlobal
          setFidesGlobal(window.Fides as InitializedFidesGlobal);
        }
        setTrigger(undefined);
      });
      setDraftIds(enabledIds);
    },
    [
      experienceFull,
      experienceMinimal,
      privacyNoticesWithBestTranslation,
      fidesGlobal,
      servingComponentRef,
      triggerRef,
      setTrigger,
      setFidesGlobal,
    ],
  );

  const handleAcceptAll = useCallback(
    (wasAutomated?: boolean) => {
      let allIds: EnabledIds;
      let exp = experienceFull || experienceMinimal;
      const enabledActiveNotices = privacyNoticesWithBestTranslation.filter(
        (n) => !n.disabled || draftIds.customPurposesConsent.includes(n.id),
      );
      if (!exp.minimal_tcf) {
        exp = experienceFull as PrivacyExperience;
        allIds = {
          purposesConsent: getAllIds(exp.tcf_purpose_consents),
          customPurposesConsent: getAllIds(enabledActiveNotices),
          purposesLegint: getAllIds(exp.tcf_purpose_legitimate_interests),
          specialPurposes: getAllIds(exp.tcf_special_purposes),
          features: getAllIds(exp.tcf_features),
          specialFeatures: getAllIds(exp.tcf_special_features),
          vendorsConsent: getAllIds([
            ...(exp.tcf_vendor_consents || []),
            ...(exp.tcf_system_consents || []),
          ]),
          vendorsLegint: getAllIds([
            ...(exp.tcf_vendor_legitimate_interests || []),
            ...(exp.tcf_system_legitimate_interests || []),
          ]),
        };
      } else {
        // eslint-disable-next-line no-param-reassign
        exp = experienceMinimal as PrivacyExperienceMinimal;
        allIds = {
          purposesConsent:
            exp.tcf_purpose_consent_ids?.map((id) => `${id}`) || [],
          customPurposesConsent: getAllIds(enabledActiveNotices) || [],
          purposesLegint:
            exp.tcf_purpose_legitimate_interest_ids?.map((id) => `${id}`) || [],
          specialPurposes:
            exp.tcf_special_purpose_ids?.map((id) => `${id}`) || [],
          features: exp.tcf_feature_ids?.map((id) => `${id}`) || [],
          specialFeatures:
            exp.tcf_special_feature_ids?.map((id) => `${id}`) || [],
          vendorsConsent: [
            ...(exp.tcf_vendor_consent_ids || []),
            ...(exp.tcf_system_consent_ids || []),
          ],
          vendorsLegint: [
            ...(exp.tcf_vendor_legitimate_interest_ids || []),
            ...(exp.tcf_system_legitimate_interest_ids || []),
          ],
        };
      }

      handleUpdateAllPreferences(
        wasAutomated ? ConsentMethod.SCRIPT : ConsentMethod.ACCEPT,
        allIds,
      );
    },
    [
      draftIds.customPurposesConsent,
      experienceFull,
      experienceMinimal,
      handleUpdateAllPreferences,
      privacyNoticesWithBestTranslation,
    ],
  );

  const handleRejectAll = useCallback(
    (wasAutomated?: boolean) => {
      // Notice-only and disabled custom purposes should not be rejected
      const enabledIds: EnabledIds = EMPTY_ENABLED_IDS;
      enabledIds.customPurposesConsent =
        privacyNoticesWithBestTranslation
          .filter((n) => {
            return (
              n.consent_mechanism === ConsentMechanism.NOTICE_ONLY ||
              (n.disabled && draftIds.customPurposesConsent.includes(n.id))
            );
          })
          .map((n) => n.id) ?? EMPTY_ENABLED_IDS;
      if (
        experienceFull?.experience_config?.reject_all_mechanism ===
        RejectAllMechanism.REJECT_CONSENT_ONLY
      ) {
        // Do not reject legitimate interests if the reject all mechanism is set to "Reject Consent Only"
        enabledIds.purposesLegint = draftIds.purposesLegint;
        enabledIds.vendorsLegint = draftIds.vendorsLegint;
        fidesDebugger(
          "Reject all mechanism is set to 'Reject Consent Only'. Ignoring legitimate interests during opt out.",
          enabledIds,
          draftIds,
        );
      }
      handleUpdateAllPreferences(
        wasAutomated ? ConsentMethod.SCRIPT : ConsentMethod.REJECT,
        enabledIds,
      );
    },
    [
      draftIds,
      experienceFull?.experience_config?.reject_all_mechanism,
      handleUpdateAllPreferences,
      privacyNoticesWithBestTranslation,
    ],
  );

  useEffect(() => {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options.fidesConsentOverride]);

  const initialTab = parseModalDefaultView(options.fidesModalDefaultView);
  const [activeTabIndex, setActiveTabIndex] = useState(initialTab);

  const dispatchOpenBannerEvent = useCallback(() => {
    setServingComponent(ServingComponent.TCF_BANNER);
    dispatchFidesEventAndClearTrigger("FidesUIShown", cookie);
  }, [cookie, dispatchFidesEventAndClearTrigger, setServingComponent]);

  const dispatchOpenOverlayEvent = useCallback(
    (origin?: string) => {
      setServingComponent(ServingComponent.TCF_OVERLAY);
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
      handleUpdateAllPreferences(ConsentMethod.DISMISS, draftIds);
    }
  }, [handleUpdateAllPreferences, draftIds, parsedCookie?.consent]);

  const handleToggleChange = useCallback(
    (updatedIds: EnabledIds, preference: FidesEventDetailsPreference) => {
      const eventExtraDetails: FidesEvent["detail"]["extraDetails"] = {
        servingComponent:
          servingComponentRef.current as FidesEventDetailsServingComponent,
        trigger: triggerRef.current,
        preference,
      };
      setDraftIds(updatedIds);
      dispatchFidesEvent("FidesUIChanged", cookie, eventExtraDetails);
    },
    [cookie, setDraftIds, triggerRef, servingComponentRef],
  );

  const handleTabChange = useCallback(
    (tabIndex: number) => {
      setActiveTabIndex(tabIndex);
    },
    [setActiveTabIndex],
  );

  const experienceConfig =
    experienceFull?.experience_config || experienceMinimal.experience_config;
  if (!experienceConfig) {
    fidesDebugger("No experience config found");
    return null;
  }

  const isDismissable = !!experienceConfig.dismissable;

  return (
    <Overlay
      options={options}
      experience={experienceFull || experienceMinimal}
      cookie={cookie}
      savedConsent={savedConsent}
      onVendorPageClick={() => {
        setActiveTabIndex(2);
      }}
      isUiBlocking={!isDismissable}
      onOpen={dispatchOpenOverlayEvent}
      onDismiss={handleDismiss}
      renderBanner={({
        attributes,
        isEmbedded,
        isOpen,
        onClose,
        onManagePreferencesClick,
      }) => {
        const goToVendorTab = () => {
          onManagePreferencesClick();
          setActiveTabIndex(2);
        };
        return (
          <ConsentBanner
            attributes={attributes}
            dismissable={isDismissable}
            bannerIsOpen={isOpen}
            isEmbedded={isEmbedded}
            onOpen={dispatchOpenBannerEvent}
            onClose={() => {
              handleDismiss();
              onClose();
            }}
            onVendorPageClick={goToVendorTab}
            renderButtonGroup={() => (
              <TcfConsentButtons
                experience={experienceFull || experienceMinimal}
                onManagePreferencesClick={onManagePreferencesClick}
                onAcceptAll={() => {
                  handleAcceptAll();
                  onClose();
                }}
                onRejectAll={() => {
                  handleRejectAll();
                  onClose();
                }}
                options={options}
              />
            )}
            className="fides-tcf-banner-container"
          >
            <TCFBannerSupplemental
              purposes={purposes}
              customPurposes={customPurposes}
            />
          </ConsentBanner>
        );
      }}
      renderModalContent={() => (
        <TcfTabs
          experience={experienceFull || experienceMinimal}
          customNotices={privacyNoticesWithBestTranslation}
          enabledIds={draftIds}
          onChange={handleToggleChange}
          activeTabIndex={activeTabIndex}
          onTabChange={handleTabChange}
          fullExperienceState={fullExperienceState}
        />
      )}
      renderModalFooter={({ onClose }) => {
        const onSave = (consentMethod: ConsentMethod, keys: EnabledIds) => {
          handleUpdateAllPreferences(consentMethod, keys);
          markSaved();
          onClose();
        };
        return (
          <TcfConsentButtons
            experience={experienceFull || experienceMinimal}
            onAcceptAll={() => {
              handleAcceptAll();
              onClose();
            }}
            onRejectAll={() => {
              handleRejectAll();
              onClose();
            }}
            renderFirstButton={() => (
              <Button
                buttonType={ButtonType.SECONDARY}
                label={
                  experienceFull ? i18n.t("exp.save_button_label") : "Save"
                }
                onClick={() => {
                  setTrigger({
                    type: FidesEventTargetType.BUTTON,
                    label: i18n.t("exp.save_button_label"),
                  });
                  onSave(ConsentMethod.SAVE, draftIds);
                }}
                className="fides-save-button"
                id="fides-save-button"
                disabled={
                  (!experienceFull &&
                    fullExperienceState === FetchState.Loading) ||
                  fullExperienceState === FetchState.Error
                }
                loading={
                  !experienceFull && fullExperienceState === FetchState.Loading
                }
                complete={isSaved}
              />
            )}
            isInModal
            options={options}
          />
        );
      }}
    />
  );
};
