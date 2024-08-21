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
import { debugLog } from "../../lib/consent-utils";
import { transformTcfPreferencesToCookieKeys } from "../../lib/cookie";
import { dispatchFidesEvent } from "../../lib/events";
import { useNoticesServed } from "../../lib/hooks";
import {
  loadMessagesFromGVLTranslations,
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
import { fetchGvlTranslations } from "../../services/api";
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
  experience: PrivacyExperience | PrivacyExperienceMinimal;
}
const TcfOverlay: FunctionComponent<TcfOverlayProps> = ({
  options,
  experience,
  i18n,
  fidesRegionString,
  cookie,
  savedConsent,
}) => {
  const experienceMinimal = experience as PrivacyExperienceMinimal;

  const { setVendorCount } = useVendorButton();

  const initialEnabledIds: EnabledIds = useMemo(() => {
    if (experienceMinimal.minimal_tcf) {
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
  }, [experience, experienceMinimal.minimal_tcf]);

  const [draftIds, setDraftIds] = useState<EnabledIds>(initialEnabledIds);

  const { currentLocale, setCurrentLocale, setIsLoading } = useI18n();

  const { locale, getDefaultLocale } = i18n;
  const defaultLocale = getDefaultLocale();

  const loadGVLTranslations = async () => {
    setIsLoading(true);
    const gvlTranslations = await fetchGvlTranslations(
      options.fidesApiUrl,
      [locale],
      options.debug,
    );
    setIsLoading(false);
    if (gvlTranslations) {
      loadMessagesFromGVLTranslations(i18n, gvlTranslations, [locale]);
      debugLog(options.debug, `Fides GVL translations loaded for ${locale}`);
    }
    setCurrentLocale(locale);
  };

  useEffect(() => {
    if (experienceMinimal.vendor_count && setVendorCount) {
      setVendorCount(experienceMinimal.vendor_count);
    }
  }, [experienceMinimal, setVendorCount]);

  useEffect(() => {
    if (!currentLocale && locale && defaultLocale) {
      if (locale !== defaultLocale) {
        loadGVLTranslations();
      } else {
        setCurrentLocale(locale);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentLocale, locale, defaultLocale, setCurrentLocale]);

  // Determine which ExperienceConfig history ID should be used for the
  // reporting APIs, based on the selected locale
  const privacyExperienceConfigHistoryId: string | undefined = useMemo(() => {
    if (experience.experience_config) {
      const bestTranslation = selectBestExperienceConfigTranslation(
        i18n,
        experience.experience_config,
      );
      return bestTranslation?.privacy_experience_config_history_id;
    }
    return undefined;
  }, [experience, i18n]);

  const tcfNoticesServed = constructTCFNoticesServedProps(
    experience || experienceMinimal,
  );

  const { servedNoticeHistoryId } = useNoticesServed({
    privacyExperienceConfigHistoryId,
    privacyNoticeHistoryIds: [],
    options,
    userGeography: fidesRegionString,
    acknowledgeMode: false,
    privacyExperience: experienceMinimal || experience,
    tcfNoticesServed,
  });

  const handleUpdateAllPreferences = useCallback(
    (consentMethod: ConsentMethod, enabledIds: EnabledIds) => {
      if (experienceMinimal.minimal_tcf) {
        return;
      }
      const experienceFull = experience as PrivacyExperience;
      const tcf = createTcfSavePayload({
        experience: experienceFull,
        enabledIds,
      });
      updateConsentPreferences({
        consentPreferencesToSave: [],
        privacyExperienceConfigHistoryId,
        experience: experienceFull,
        consentMethod,
        options,
        userLocationString: fidesRegionString,
        cookie,
        debug: options.debug,
        tcf,
        servedNoticeHistoryId,
        updateCookie: (oldCookie) =>
          updateCookie(oldCookie, tcf, enabledIds, experienceFull),
      });
      setDraftIds(enabledIds);
    },
    [
      cookie,
      experience,
      experienceMinimal.minimal_tcf,
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
    experienceMinimal.experience_config || experience.experience_config;
  if (!experienceConfig) {
    debugLog(options.debug, "No experience config found");
    return null;
  }

  const isDismissable = !!experienceConfig.dismissable;

  return (
    <Overlay
      options={options}
      experience={experienceMinimal || experience}
      i18n={i18n}
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
            i18n={i18n}
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
                experience={experienceMinimal || experience}
                i18n={i18n}
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
            <TCFBannerSupplemental />
          </ConsentBanner>
        );
      }}
      renderModalContent={
        experienceMinimal.minimal_tcf
          ? undefined
          : () => (
              <TcfTabs
                i18n={i18n}
                experience={experience as PrivacyExperience}
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
        experienceMinimal.minimal_tcf
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
                  i18n={i18n}
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
