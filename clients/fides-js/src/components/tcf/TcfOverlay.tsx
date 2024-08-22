import "../fides.css";
import "./fides-tcf.css";

import { FunctionComponent, h } from "preact";
import { useCallback, useEffect, useMemo, useState } from "preact/hooks";

import {
  ButtonType,
  ConsentMethod,
  FidesCookie,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  ServingComponent,
} from "../../lib/consent-types";
import { debugLog, isPrivacyExperience } from "../../lib/consent-utils";
import { transformTcfPreferencesToCookieKeys } from "../../lib/cookie";
import { dispatchFidesEvent } from "../../lib/events";
import { useNoticesServed } from "../../lib/hooks";
import {
  loadGVLMessagesFromExperience,
  loadMessagesFromExperience,
  loadMessagesFromGVLTranslations,
  matchAvailableLocales,
  selectBestExperienceConfigTranslation,
} from "../../lib/i18n";
import { useI18n } from "../../lib/i18n/i18n-context";
import { updateConsentPreferences } from "../../lib/preferences";
import {
  transformConsentToFidesUserPreference,
  transformUserPreferenceToBoolean,
} from "../../lib/shared-consent-utils";
import { generateFidesString } from "../../lib/tcf";
import type {
  EnabledIds,
  TCFFeatureRecord,
  TCFFeatureSave,
  TcfModels,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFPurposeSave,
  TcfSavePreferences,
  TCFSpecialFeatureSave,
  TCFSpecialPurposeSave,
  TCFVendorConsentRecord,
  TCFVendorLegitimateInterestsRecord,
  TCFVendorSave,
} from "../../lib/tcf/types";
import { constructTCFNoticesServedProps } from "../../lib/tcf/utils";
import { useVendorButton } from "../../lib/tcf/vendor-button-context";
import { fetchExperience, fetchGvlTranslations } from "../../services/api";
import Button from "../Button";
import ConsentBanner from "../ConsentBanner";
import Overlay from "../Overlay";
import { OverlayProps } from "../types";
import { TCFBannerSupplemental } from "./TCFBannerSupplemental";
import { TcfConsentButtons } from "./TcfConsentButtons";
import TcfTabs from "./TcfTabs";

const resolveConsentValueFromTcfModel = (
  model:
    | TCFPurposeConsentRecord
    | TCFPurposeLegitimateInterestsRecord
    | TCFFeatureRecord
    | TCFVendorConsentRecord
    | TCFVendorLegitimateInterestsRecord,
) => {
  if (model.current_preference) {
    return transformUserPreferenceToBoolean(model.current_preference);
  }

  return transformUserPreferenceToBoolean(model.default_preference);
};

type TcfSave =
  | TCFPurposeSave
  | TCFSpecialPurposeSave
  | TCFFeatureSave
  | TCFSpecialFeatureSave
  | TCFVendorSave;

const getEnabledIds = (modelList: TcfModels) => {
  if (!modelList) {
    return [];
  }
  return modelList
    .map((model) => {
      const value = resolveConsentValueFromTcfModel(model);
      return { ...model, consentValue: value };
    })
    .filter((model) => model.consentValue)
    .map((model) => `${model.id}`);
};

const transformTcfModelToTcfSave = ({
  modelList,
  enabledIds,
}: {
  modelList: TcfModels;
  enabledIds: string[];
}): TcfSave[] | null => {
  if (!modelList) {
    return [];
  }
  return modelList.map((model) => {
    const preference = transformConsentToFidesUserPreference(
      enabledIds.includes(`${model.id}`),
    );
    return {
      id: model.id,
      preference,
    };
  }) as TcfSave[];
};

const createTcfSavePayload = ({
  experience,
  enabledIds,
}: {
  experience: PrivacyExperience;
  enabledIds: EnabledIds;
}): TcfSavePreferences => {
  const {
    tcf_system_consents: consentSystems,
    tcf_system_legitimate_interests: legintSystems,
  } = experience;
  // Because systems were combined with vendors to make the UI easier to work with,
  // we need to separate them out now (the backend treats them as separate entities).
  const enabledConsentSystemIds: string[] = [];
  const enabledConsentVendorIds: string[] = [];
  const enabledLegintSystemIds: string[] = [];
  const enabledLegintVendorIds: string[] = [];
  enabledIds.vendorsConsent.forEach((id) => {
    if (consentSystems?.map((s) => s.id).includes(id)) {
      enabledConsentSystemIds.push(id);
    } else {
      enabledConsentVendorIds.push(id);
    }
  });
  enabledIds.vendorsLegint.forEach((id) => {
    if (legintSystems?.map((s) => s.id).includes(id)) {
      enabledLegintSystemIds.push(id);
    } else {
      enabledLegintVendorIds.push(id);
    }
  });

  return {
    purpose_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_purpose_consents,
      enabledIds: enabledIds.purposesConsent,
    }) as TCFPurposeSave[],
    purpose_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_purpose_legitimate_interests,
      enabledIds: enabledIds.purposesLegint,
    }) as TCFPurposeSave[],
    special_feature_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_special_features,
      enabledIds: enabledIds.specialFeatures,
    }) as TCFSpecialFeatureSave[],
    vendor_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_vendor_consents,
      enabledIds: enabledConsentVendorIds,
    }) as TCFVendorSave[],
    vendor_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_vendor_legitimate_interests,
      enabledIds: enabledLegintVendorIds,
    }) as TCFVendorSave[],
    system_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_system_consents,
      enabledIds: enabledConsentSystemIds,
    }) as TCFVendorSave[],
    system_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_system_legitimate_interests,
      enabledIds: enabledLegintSystemIds,
    }) as TCFVendorSave[],
  };
};

const updateCookie = async (
  oldCookie: FidesCookie,
  /**
   * `tcf` and `enabledIds` should represent the same data, where `tcf` is what is
   * sent to the backend, and `enabledIds` is what the FE uses. They have diverged
   * because the backend has not implemented separate vendor legint/consents yet.
   * Therefore, we need both entities right now, but eventually we should be able to
   * only use one. In other words, `enabledIds` has a field for `vendorsConsent` and
   * `vendorsLegint` but `tcf` only has `vendors`.
   */
  tcf: TcfSavePreferences,
  enabledIds: EnabledIds,
  experience: PrivacyExperience,
): Promise<FidesCookie> => {
  const tcString = await generateFidesString({
    tcStringPreferences: enabledIds,
    experience,
  });
  return {
    ...oldCookie,
    fides_string: tcString,
    tcf_consent: transformTcfPreferencesToCookieKeys(tcf),
    tcf_version_hash: experience.meta?.version_hash,
  };
};

interface TcfOverlayProps extends Omit<OverlayProps, "experience"> {
  experienceMinimal: PrivacyExperienceMinimal;
}
const TcfOverlay: FunctionComponent<TcfOverlayProps> = ({
  options,
  experienceMinimal,
  fidesRegionString,
  cookie,
  savedConsent,
  propertyId,
}) => {
  const {
    i18n,
    currentLocale,
    setCurrentLocale,
    setIsLoading: setIsI18nLoading,
  } = useI18n();
  const minExperienceLocale =
    experienceMinimal?.experience_config?.translations?.[0]?.language;
  const defaultLocale = i18n.getDefaultLocale();
  const bestLocale = matchAvailableLocales(
    options.fidesLocale || i18n.locale,
    experienceMinimal.available_locales || [],
    i18n.getDefaultLocale(),
  );

  useEffect(() => {
    if (!currentLocale) {
      // initialize the i18n locale using the minimal experience
      setCurrentLocale(minExperienceLocale);
    }
  }, [currentLocale, minExperienceLocale, setCurrentLocale]);

  const loadGVLTranslations = async (locale: string) => {
    const gvlTranslations = await fetchGvlTranslations(
      options.fidesApiUrl,
      [locale],
      options.debug,
    );
    if (gvlTranslations) {
      loadMessagesFromGVLTranslations(i18n, gvlTranslations, [locale]);
      debugLog(options.debug, `Fides GVL translations loaded for ${locale}`);
    }
  };

  /**
   * TCF overlay loads with a minimal experience, which is then replaced with the full.
   * We do this to ensure the overlay can be rendered as quickly as possible.
   * The full experience is fetched after the component mounts, so we store it
   * in state to trigger a re-render when it arrives.
   */
  const [experience, setExperience] = useState<PrivacyExperience>();

  useEffect(() => {
    // We need to track if the experience and GVL translations are loading separately
    // because they are loaded asynchronously and we need to know when both are done
    // in order to set the i18n loading state.
    let isExperienceLoading = false;
    let isGVLLangLoading = false;

    if (!!options.fidesLocale && options.fidesLocale !== minExperienceLocale) {
      // the minimal experience language is different from the configured language.
      // This occurs when the customer has set their overrides on the window object
      // which isn't available to us until the experience is fetched. In this case,
      // we'll get the translations for the banner from the full experience.
      setIsI18nLoading(true);
    }
    if (!!options.fidesLocale && options.fidesLocale !== defaultLocale) {
      // We can only get default locale (English) GVL translations from the experience.
      // If the configured locale is not the default, we need to load the translations
      // from the api.
      setIsI18nLoading(true);
      isGVLLangLoading = true;
      loadGVLTranslations(bestLocale).then(() => {
        isGVLLangLoading = false;
        if (!isExperienceLoading) {
          setIsI18nLoading(false);
        }
      });
    }
    isExperienceLoading = true;
    fetchExperience({
      userLocationString: fidesRegionString,
      fidesApiUrl: options.fidesApiUrl,
      debug: options.debug,
      apiOptions: options.apiOptions,
      propertyId,
      minimalTCF: false,
    }).then((result) => {
      if (isPrivacyExperience(result)) {
        setExperience(result);
        loadMessagesFromExperience(i18n, result);
        isExperienceLoading = false;
        if (options.fidesLocale === defaultLocale) {
          // English (default) GVL translations are part of the full experience, so we load them here.
          loadGVLMessagesFromExperience(i18n, result);
        } else {
          setCurrentLocale(bestLocale);
          if (!isGVLLangLoading) {
            setIsI18nLoading(false);
          }
        }
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const { setVendorCount } = useVendorButton();

  const initialEnabledIds: EnabledIds = useMemo(() => {
    if (!experience) {
      return {
        purposesConsent: [],
        purposesLegint: [],
        specialPurposes: [],
        features: [],
        specialFeatures: [],
        vendorsConsent: [],
        vendorsLegint: [],
      };
    }
    const {
      tcf_purpose_consents: consentPurposes = [],
      tcf_purpose_legitimate_interests: legintPurposes = [],
      tcf_special_purposes: specialPurposes = [],
      tcf_features: features = [],
      tcf_special_features: specialFeatures = [],
      tcf_vendor_consents: consentVendors = [],
      tcf_vendor_legitimate_interests: legintVendors = [],
      tcf_system_consents: consentSystems = [],
      tcf_system_legitimate_interests: legintSystems = [],
    } = experience as PrivacyExperience;

    // Vendors and systems are the same to the FE, so we combine them here
    return {
      purposesConsent: getEnabledIds(consentPurposes),
      purposesLegint: getEnabledIds(legintPurposes),
      specialPurposes: getEnabledIds(specialPurposes),
      features: getEnabledIds(features),
      specialFeatures: getEnabledIds(specialFeatures),
      vendorsConsent: getEnabledIds([...consentVendors, ...consentSystems]),
      vendorsLegint: getEnabledIds([...legintVendors, ...legintSystems]),
    };
  }, [experience]);

  const [draftIds, setDraftIds] = useState<EnabledIds>(initialEnabledIds);

  useEffect(() => {
    if (experienceMinimal.vendor_count && setVendorCount) {
      setVendorCount(experienceMinimal.vendor_count);
    }
  }, [experienceMinimal, setVendorCount]);

  // Determine which ExperienceConfig history ID should be used for the
  // reporting APIs, based on the selected locale
  const privacyExperienceConfigHistoryId: string | undefined = useMemo(() => {
    if (experienceMinimal?.experience_config) {
      const bestTranslation = selectBestExperienceConfigTranslation(
        i18n,
        experienceMinimal.experience_config,
      );
      return bestTranslation?.privacy_experience_config_history_id;
    }
    return undefined;
  }, [experienceMinimal, i18n]);

  const purposes: string[] = useMemo(() => {
    const tcfPurposeNames = experienceMinimal?.tcf_purpose_names || [];
    const tcfSpecialFeatureNames =
      experienceMinimal?.tcf_special_feature_names || [];
    return [...tcfPurposeNames, ...tcfSpecialFeatureNames];
  }, [experienceMinimal]);

  const tcfNoticesServed = constructTCFNoticesServedProps(
    experience || experienceMinimal,
  );

  const { servedNoticeHistoryId } = useNoticesServed({
    privacyExperienceConfigHistoryId,
    privacyNoticeHistoryIds: [],
    options,
    userGeography: fidesRegionString,
    acknowledgeMode: false,
    privacyExperience: experience || experienceMinimal,
    tcfNoticesServed,
  });

  const handleUpdateAllPreferences = useCallback(
    (consentMethod: ConsentMethod, enabledIds: EnabledIds) => {
      if (!experience) {
        return;
      }
      const tcf = createTcfSavePayload({
        experience,
        enabledIds,
      });
      updateConsentPreferences({
        consentPreferencesToSave: [],
        privacyExperienceConfigHistoryId,
        experience,
        consentMethod,
        options,
        userLocationString: fidesRegionString,
        cookie,
        debug: options.debug,
        tcf,
        servedNoticeHistoryId,
        updateCookie: (oldCookie) =>
          updateCookie(oldCookie, tcf, enabledIds, experience),
      });
      setDraftIds(enabledIds);
    },
    [
      cookie,
      experience,
      fidesRegionString,
      options,
      privacyExperienceConfigHistoryId,
      servedNoticeHistoryId,
    ],
  );

  const [activeTabIndex, setActiveTabIndex] = useState(0);

  const dispatchOpenBannerEvent = useCallback(() => {
    dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
      servingComponent: ServingComponent.TCF_BANNER,
    });
  }, [cookie, options.debug]);

  const dispatchOpenOverlayEvent = useCallback(() => {
    dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
      servingComponent: ServingComponent.TCF_OVERLAY,
    });
  }, [cookie, options.debug]);

  const handleDismiss = useCallback(() => {
    handleUpdateAllPreferences(ConsentMethod.DISMISS, initialEnabledIds);
  }, [handleUpdateAllPreferences, initialEnabledIds]);

  const experienceConfig =
    experience?.experience_config || experienceMinimal.experience_config;
  if (!experienceConfig) {
    debugLog(options.debug, "No experience config found");
    return null;
  }

  const isDismissable = !!experienceConfig.dismissable;

  return (
    <Overlay
      options={options}
      experience={experience || experienceMinimal}
      cookie={cookie}
      savedConsent={savedConsent}
      onVendorPageClick={() => {
        setActiveTabIndex(2);
      }}
      isUiBlocking={!isDismissable}
      onOpen={dispatchOpenOverlayEvent}
      onDismiss={handleDismiss}
      renderBanner={({
        isEmbedded,
        isOpen,
        onClose,
        onSave,
        onManagePreferencesClick,
      }) => {
        const goToVendorTab = () => {
          onManagePreferencesClick();
          setActiveTabIndex(2);
        };
        return (
          <ConsentBanner
            dismissable={isDismissable}
            bannerIsOpen={isOpen}
            isEmbedded={isEmbedded}
            onOpen={dispatchOpenBannerEvent}
            onClose={() => {
              onClose();
              handleDismiss();
            }}
            onVendorPageClick={goToVendorTab}
            renderButtonGroup={() => (
              <TcfConsentButtons
                experience={experience || experienceMinimal}
                onManagePreferencesClick={onManagePreferencesClick}
                onSave={(consentMethod: ConsentMethod, keys: EnabledIds) => {
                  handleUpdateAllPreferences(consentMethod, keys);
                  onSave();
                }}
                options={options}
              />
            )}
            className="fides-tcf-banner-container"
          >
            <TCFBannerSupplemental purposes={purposes} />
          </ConsentBanner>
        );
      }}
      renderModalContent={
        !experience
          ? undefined
          : () => (
              <TcfTabs
                experience={experience}
                enabledIds={draftIds}
                onChange={(updatedIds) => {
                  setDraftIds(updatedIds);
                  dispatchFidesEvent("FidesUIChanged", cookie, options.debug);
                }}
                activeTabIndex={activeTabIndex}
                onTabChange={setActiveTabIndex}
              />
            )
      }
      renderModalFooter={
        !experience
          ? undefined
          : ({ onClose }) => {
              const onSave = (
                consentMethod: ConsentMethod,
                keys: EnabledIds,
              ) => {
                handleUpdateAllPreferences(consentMethod, keys);
                onClose();
              };
              return (
                <TcfConsentButtons
                  experience={experience}
                  onSave={onSave}
                  renderFirstButton={() => (
                    <Button
                      buttonType={ButtonType.SECONDARY}
                      label={i18n.t("exp.save_button_label")}
                      onClick={() => onSave(ConsentMethod.SAVE, draftIds)}
                      className="fides-save-button"
                    />
                  )}
                  isInModal
                  options={options}
                />
              );
            }
      }
    />
  );
};

export default TcfOverlay;
