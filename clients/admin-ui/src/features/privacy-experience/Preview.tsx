import { useToast } from "@fidesui/react";
import {
  CookieKeyConsent,
  EmptyExperience,
  FidesOptions,
  PrivacyExperience,
  UserGeolocation,
} from "fides-js/src/lib/consent-types";
import { useFormikContext } from "formik";
import Script from "next/script";
import React, { useEffect, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { TranslationWithLanguageName } from "~/features/privacy-experience/form/helpers";
import { useLazyGetPrivacyNoticeByIdQuery } from "~/features/privacy-notices/privacy-notices.slice";
import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceTranslation,
  LimitedPrivacyNoticeResponseSchema,
  PrivacyNoticeResponse,
  SupportedLanguage,
} from "~/types/api";

export type Fides = {
  consent: CookieKeyConsent;
  experience?: PrivacyExperience | EmptyExperience;
  geolocation?: UserGeolocation;
  options: FidesOptions;
  init: (config: any) => {};
};

declare global {
  interface Window {
    Fides: Fides;
  }
}

enum FidesPreviewComponent {
  BANNER = "banner",
  MODAL = "modal",
}

const Preview = ({
  allPrivacyNotices,
  initialValues,
  translation,
  isMobilePreview,
}: {
  allPrivacyNotices: Partial<LimitedPrivacyNoticeResponseSchema[]>;
  initialValues: Partial<ExperienceConfigCreate>;
  translation?: TranslationWithLanguageName;
  isMobilePreview: boolean;
}) => {
  const { values } = useFormikContext<ExperienceConfigCreate>();
  const [noticesOnConfig, setNoticesOnConfig] = useState<
    PrivacyNoticeResponse[]
  >([]);

  const toast = useToast();

  const [getPrivacyNoticeByIdTrigger] = useLazyGetPrivacyNoticeByIdQuery();

  const getPrivacyNotice = async (id: string) => {
    const result = await getPrivacyNoticeByIdTrigger(id);
    if (result.isError) {
      const errorMsg = getErrorMessage(
        result.error,
        "A problem occurred while fetching privacy notice data.  Some notices may not display correctly on the preview."
      );
      toast({ status: "error", description: errorMsg });
    }
    const { data } = await getPrivacyNoticeByIdTrigger(id);
    return data;
  };

  useEffect(() => {
    Promise.all(
      values.privacy_notice_ids!.map((id) => getPrivacyNotice(id))
    ).then((data) =>
      // TS can't tell that we filter out notices that are undefined here
      // @ts-ignore
      setNoticesOnConfig(data.filter((notice) => notice !== undefined))
    );
    // ESLint wants us to have getPrivacyNotice in the dependencies, but doing
    // so makes the privacy notice queries fire on every re-render;
    // we can omit it because it isn't calculated from state or props
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [values.privacy_notice_ids]);

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
      privacy_notices: noticesOnConfig,
    },
    geolocation: {
      country: "US",
      location: "US-CA",
      region: "CA",
    },
  };

  useEffect(() => {
    // if current component is a modal, we want to force fides.js to show a modal, not a banner component
    if (values.component === ComponentType.MODAL) {
      baseConfig.options.fidesPreviewComponent = FidesPreviewComponent.MODAL;
    }
    // if we're editing a translation, we want to preview the banner/modal with that language,
    // otherwise we show first translation if exists, else keep default
    const currentTranslation: ExperienceTranslation | undefined = translation
      ? values.translations?.filter(
          (i) => i.language === translation.language
        )[0]
      : undefined;
    if (currentTranslation) {
      baseConfig.experience.experience_config.translations[0] =
        currentTranslation;
    } else if (values.translations) {
      // eslint-disable-next-line prefer-destructuring
      baseConfig.experience.experience_config.translations[0] =
        values.translations[0];
    }
    baseConfig.options.preventDismissal = !values.dismissable;
    if (window.Fides) {
      window.Fides.init(baseConfig);
    }
  }, [values, translation, baseConfig, allPrivacyNotices]);

  return (
    <>
      {/* style overrides for preview model */}
      <style jsx global>{`
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
        <style>{`
            div#preview-container {
              width: 70% !important;
            }
            `}</style>
      ) : (
        <style>{`
            div#fides-banner {
              width: 90% !important;
            }
            `}</style>
      )}
      <Script
        id="fides-js-base"
        src={fidesJsScript}
        onReady={() => {
          window.Fides?.init(baseConfig);
        }}
      />
      <div id="preview-container" />
    </>
  );
};

export default Preview;
