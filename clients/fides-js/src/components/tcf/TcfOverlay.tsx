import "../fides.css";
import "./fides-tcf.css";

import { h } from "preact";
import { useCallback, useEffect, useMemo, useState } from "preact/hooks";

import {
  ButtonType,
  ConsentMethod,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  ServingComponent,
} from "../../lib/consent-types";
import { isPrivacyExperience } from "../../lib/consent-utils";
import { dispatchFidesEvent } from "../../lib/events";
import { useNoticesServed } from "../../lib/hooks";
import {
  DEFAULT_LOCALE,
  detectUserLocale,
  loadGVLMessagesFromExperience,
  loadMessagesFromExperience,
  loadMessagesFromGVLTranslations,
  matchAvailableLocales,
  selectBestExperienceConfigTranslation,
} from "../../lib/i18n";
import { useI18n } from "../../lib/i18n/i18n-context";
import { updateConsentPreferences } from "../../lib/preferences";
import { useGvl } from "../../lib/tcf/gvl-context";
import type { EnabledIds, TcfSavePreferences } from "../../lib/tcf/types";
import {
  buildTcfEntitiesFromCookieAndFidesString as buildUserPrefs,
  constructTCFNoticesServedProps,
  createTcfSavePayload,
  createTcfSavePayloadFromMinExp,
  getEnabledIds,
  getGVLPurposeList,
  updateCookie,
} from "../../lib/tcf/utils";
import { useVendorButton } from "../../lib/tcf/vendor-button-context";
import { fetchExperience, fetchGvlTranslations } from "../../services/api";
import Button from "../Button";
import ConsentBanner from "../ConsentBanner";
import Overlay from "../Overlay";
import { OverlayProps } from "../types";
import { TCFBannerSupplemental } from "./TCFBannerSupplemental";
import { TcfConsentButtons } from "./TcfConsentButtons";
import TcfTabs from "./TcfTabs";

interface TcfOverlayProps extends Omit<OverlayProps, "experience"> {
  experienceMinimal: PrivacyExperienceMinimal;
}
export const TcfOverlay = ({
  options,
  experienceMinimal,
  fidesRegionString,
  cookie,
  savedConsent,
  propertyId,
  translationOverrides,
}: TcfOverlayProps) => {
  const {
    i18n,
    currentLocale,
    setCurrentLocale,
    setIsLoading: setIsI18nLoading,
  } = useI18n();
  const minExperienceLocale =
    experienceMinimal?.experience_config?.translations?.[0]?.language;
  const defaultLocale = i18n.getDefaultLocale();
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
   * TCF overlay loads with a minimal experience, which is then replaced with the full.
   * We do this to ensure the overlay can be rendered as quickly as possible.
   * The full experience is fetched after the component mounts, so we store it
   * in state to trigger a re-render when it arrives.
   */
  const [experience, setExperience] = useState<PrivacyExperience>();

  useEffect(() => {
    let isGVLLangLoading = false;

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
      isGVLLangLoading = true;
      loadGVLTranslations(bestLocale).then(() => {
        isGVLLangLoading = false;
      });
    }
    fetchExperience({
      userLocationString: fidesRegionString,
      fidesApiUrl: options.fidesApiUrl,
      apiOptions: options.apiOptions,
      propertyId,
      requestMinimalTCF: false,
    }).then((result) => {
      if (isPrivacyExperience(result)) {
        // include user preferences from the cookie
        const userPrefs = buildUserPrefs(result, cookie);
        const fullExperience: PrivacyExperience = { ...result, ...userPrefs };

        setExperience(fullExperience);
        loadMessagesFromExperience(i18n, fullExperience, translationOverrides);
        if (!userlocale || bestLocale === defaultLocale) {
          // English (default) GVL translations are part of the full experience, so we load them here.
          loadGVLMessagesFromExperience(i18n, fullExperience);
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

  const [draftIds, setDraftIds] = useState<EnabledIds>();

  useEffect(() => {
    if (!experience) {
      setDraftIds({
        purposesConsent: [],
        purposesLegint: [],
        specialPurposes: [],
        features: [],
        specialFeatures: [],
        vendorsConsent: [],
        vendorsLegint: [],
      });
    } else {
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
      setDraftIds({
        purposesConsent: getEnabledIds(consentPurposes),
        purposesLegint: getEnabledIds(legintPurposes),
        specialPurposes: getEnabledIds(specialPurposes),
        features: getEnabledIds(features),
        specialFeatures: getEnabledIds(specialFeatures),
        vendorsConsent: getEnabledIds([...consentVendors, ...consentSystems]),
        vendorsLegint: getEnabledIds([...legintVendors, ...legintSystems]),
      });
    }
  }, [experience]);

  useEffect(() => {
    if (experienceMinimal.vendor_count && setVendorCount) {
      setVendorCount(experienceMinimal.vendor_count);
    }
  }, [experienceMinimal, setVendorCount]);

  // Determine which ExperienceConfig history ID should be used for the
  // reporting APIs, based on the selected locale
  const privacyExperienceConfigHistoryId: string | undefined = useMemo(() => {
    const experienceConfig =
      experience?.experience_config || experienceMinimal.experience_config;
    if (experienceConfig) {
      const bestTranslation = selectBestExperienceConfigTranslation(
        i18n,
        experienceConfig,
      );
      return bestTranslation?.privacy_experience_config_history_id;
    }
    return undefined;
  }, [experienceMinimal, experience, i18n]);

  const purposes: string[] = useMemo(() => {
    if (gvlTranslations) {
      return getGVLPurposeList(gvlTranslations);
    }
    const tcfPurposeNames = experienceMinimal?.tcf_purpose_names || [];
    const tcfSpecialFeatureNames =
      experienceMinimal?.tcf_special_feature_names || [];
    return [...tcfPurposeNames, ...tcfSpecialFeatureNames];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [experienceMinimal, gvlTranslations]);

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
      if (!experience && !experienceMinimal) {
        return;
      }
      let tcf: TcfSavePreferences;
      if (!experience && experienceMinimal?.minimal_tcf) {
        tcf = createTcfSavePayloadFromMinExp({
          experience: experienceMinimal,
          enabledIds,
        });
      } else {
        tcf = createTcfSavePayload({
          experience: experience as PrivacyExperience,
          enabledIds,
        });
      }
      updateConsentPreferences({
        consentPreferencesToSave: [],
        privacyExperienceConfigHistoryId,
        experience: experience || experienceMinimal,
        consentMethod,
        options,
        userLocationString: fidesRegionString,
        cookie,
        debug: options.debug,
        tcf,
        servedNoticeHistoryId,
        updateCookie: (oldCookie) =>
          updateCookie(
            oldCookie,
            tcf,
            enabledIds,
            experience || experienceMinimal,
          ),
      });
      setDraftIds(enabledIds);
    },
    [
      cookie,
      experience,
      experienceMinimal,
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
    handleUpdateAllPreferences(ConsentMethod.DISMISS, draftIds!);
  }, [handleUpdateAllPreferences, draftIds]);

  const experienceConfig =
    experience?.experience_config || experienceMinimal.experience_config;
  if (!experienceConfig) {
    fidesDebugger("No experience config found");
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
                enabledIds={draftIds!}
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
                      onClick={() => onSave(ConsentMethod.SAVE, draftIds!)}
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
