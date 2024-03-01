import {
  CookieKeyConsent,
  EmptyExperience,
  FidesOptions,
  PrivacyExperience,
  UserGeolocation,
} from "fides-js/src/lib/consent-types";
import {useFormikContext} from "formik";
import Script from "next/script";
import React, {useEffect} from "react";

import {TranslationWithLanguageName} from "~/features/privacy-experience/form/helpers";
import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceTranslation,
  LimitedPrivacyNoticeResponseSchema,
  SupportedLanguage,
} from "~/types/api";

export type Fides = {
  consent: CookieKeyConsent;
  experience?: PrivacyExperience | EmptyExperience;
  geolocation?: UserGeolocation;
  options: FidesOptions;
};

declare global {
  interface Window {
    Fides: Fides;
  }
}

enum FidesPreviewComponent {
  BANNER = "banner",
  MODAL = "modal"
}

const Preview = ({
    allPrivacyNotices,
  initialValues,
  translation,
    isMobilePreview
}: {
  allPrivacyNotices: Partial<LimitedPrivacyNoticeResponseSchema[]>;
  initialValues: Partial<ExperienceConfigCreate>;
  translation: TranslationWithLanguageName;
  isMobilePreview: boolean;
}) => {
  const { values } = useFormikContext<ExperienceConfigCreate>();

  const fidesJsScript = "/lib/fides.js";

  const buildExperienceTranslation = (
    config: Partial<ExperienceConfigCreate>
  ): ExperienceTranslation => ({
    language: config.translations
      ? config.translations[0].language
      : SupportedLanguage.EN,
    accept_button_label: config.translations
      ? config.translations[0].accept_button_label
      : "Accept",
    acknowledge_button_label: config.translations
      ? config.translations[0].acknowledge_button_label
      : "OK",
    banner_description: config.translations
      ? config.translations[0].banner_description
      : "",
    banner_title: config.translations
      ? config.translations[0].banner_title
      : "",
    description: config.translations ? config.translations[0].description : "",
    is_default: true,
    privacy_policy_link_label: config.translations
      ? config.translations[0].privacy_policy_link_label
      : "",
    privacy_policy_url: config.translations
      ? config.translations[0].privacy_policy_url
      : "",
    privacy_preferences_link_label: config.translations
      ? config.translations[0].privacy_preferences_link_label
      : "",
    reject_button_label: config.translations
      ? config.translations[0].reject_button_label
      : "Reject All",
    save_button_label: config.translations
      ? config.translations[0].save_button_label
      : "Save",
    title: config.translations ? config.translations[0].title : "",
  });

  const buildNotices = (config: Partial<ExperienceConfigCreate>) => {
    // how to get notices?
  };

  // Create the base FidesConfig JSON that will be used to initialize fides.js
  const baseConfig = {
    options: {
      debug: true,
      geolocationApiUrl: "",
      isGeolocationEnabled: false,
      isOverlayEnabled: true,
      isPrefetchEnabled: false,
      overlayParentId: "preview-container",
      modalLinkId: null,
      privacyCenterUrl: "http://localhost:3000",
      fidesApiUrl: "http://localhost:8080/api/v1",
      // todo- get this from config
      preventDismissal: false,
      fidesPreviewMode: true,
      fidesPreviewComponent: FidesPreviewComponent.BANNER,
      allowHTMLDescription: true,
      serverSideFidesApiUrl: "",
      fidesString: null,
      fidesJsBaseUrl: "",
      base64Cookie: false,
    },
    experience: {
      id: "pri_111",
      region: "us_ca",
      component: "banner_and_modal",
      experience_config: {
        id: "pri_222",
        regions: ["us_ca"],
        component: "banner_and_modal",
        disabled: false,
        is_default: true,
        dismissable: initialValues.dismissable,
        allow_language_selection: true,
        auto_detect_language: true,
        language: "en",
        // in preview mode, we show the first translation in the main window, even when multiple translations are configured
        translations: [buildExperienceTranslation(initialValues)],
      },
      privacy_notices: [
        {
          id: "pri_555",
          origin: "pri_xxx",
          name: "Advertising Test",
          notice_key: "advertising",
          description: "Advertising Description Test",
          internal_description: "Advertising Internal Description Test",
          consent_mechanism: "opt_in",
          data_uses: ["marketing.advertising.first_party.targeted"],
          enforcement_level: "frontend",
          disabled: false,
          has_gpc_flag: true,
          framework: null,
          default_preference: "opt_out",
          cookies: [],
          systems_applicable: false,
          translations: [
            {
              language: "en",
              title: "Advertising Test",
              description: "Advertising Description Test",
              privacy_notice_history_id: "pri_666",
            },
          ],
        },
        {
          id: "pri_888",
          origin: "pri_xxx",
          name: "Analytics Test",
          notice_key: "analytics",
          internal_description: "Analytics Internal Description",
          consent_mechanism: "opt_out",
          data_uses: ["analytics.reporting.ad_performance"],
          enforcement_level: "frontend",
          disabled: false,
          has_gpc_flag: false,
          framework: null,
          default_preference: "opt_in",
          cookies: [{ name: "_ga", path: null, domain: null }],
          systems_applicable: true,
          translations: [
            {
              language: "en",
              title: "Analytics Test",
              description: "Analytics Description Test",
              privacy_notice_history_id: "pri_999",
            },
            {
              language: "es",
              title: "Prueba de Analítica",
              description: "Descripción de la Analítica de Prueba",
              privacy_notice_history_id: "pri_000",
            },
          ],
        },
      ],
    },
    geolocation: {
      country: "US",
      location: "US-CA",
      region: "CA",
    },
  };

  useEffect(() => {
    // const element = document.getElementById("preview-container");
    // if (element) {
    //   element.removeChild(element.firstChild);
    //   console.log("removed child");
    // }
    // if component is API or privacy center don't show preview
    // todo- handle privacy notice ids
    // if we're editing a translation, we want to preview it, otherwise show first translation if exists, else keep default
    if (values.component === ComponentType.MODAL) {
      baseConfig.options.fidesPreviewComponent = FidesPreviewComponent.MODAL
    }
    if (translation) {
      const currentTranslation: ExperienceTranslation =
        values.translations?.filter(
          (i) => i.language === translation.language
        )[0];
      baseConfig.experience.experience_config.translations[0] =
        currentTranslation;
    } else if (values.translations) {
      // eslint-disable-next-line prefer-destructuring
      baseConfig.experience.experience_config.translations[0] =
        values.translations[0];
    }
    console.log(allPrivacyNotices);
    console.log(values);
    console.log(translation);
    // fixme- add privacy notices
    // if (values.privacy_notice_ids && values.privacy_notice_ids.length >= 1) {
    //   // @ts-ignore
    //   const noticesOnExperience = allPrivacyNotices.filter((n) => n.id in values.privacy_notice_ids);
    //   if (noticesOnExperience) {
    //     baseConfig.experience.privacy_notices = noticesOnExperience
    //   }
    // }
    // todo - this should remove "x" on banner / modal
    baseConfig.experience.experience_config.dismissable = values.dismissable;
    if (window.Fides) {
      window.Fides.init(baseConfig);
    }
  }, [values, translation, baseConfig, allPrivacyNotices]);

  return (
    <>
      {/* style overrides for preview model */}
      <style jsx global>{
        `
        div#fides-overlay {
          z-index: 5000 !important;
        }
        div#preview-container {
          margin: auto !important;
        }
        div#fides-banner-container {
          position: static !important;
          transform: none !important;
          transition: none !important;
        }
        div#fides-banner-container.fides-banner-hidden {
          display: none;
        }
        .fides-modal-container,
        .fides-modal-overlay {
          background-color: inherit !important;
          position: static !important;
        }
        div.fides-modal-content {
          position: relative !important;
          transform: none !important;
          left: initial !important;
          top: initial !important;
        }
      `}</style>
      {isMobilePreview ? (
          <style>{
            `
            div#preview-container {
              width: 70% !important;
            }
            `
          }</style>
      ) : (
          <style>{
            `
            div#fides-banner {
              width: 90% !important;
            }
            `
          }</style>
      )}
      <Script
        id="fides-js-base"
        src={fidesJsScript}
        onReady={() => {
          // Enable the GTM integration, if GTM is configured
          window.Fides?.init(baseConfig);
        }}
      />
      <div id="preview-container" />
    </>
  );
};

export default Preview;
