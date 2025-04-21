import { FidesGlobal } from "fides-js/src/lib/consent-types";
import { AntFlex as Flex, Text } from "fidesui";
import { useFormikContext } from "formik";
import { useRouter } from "next/router";
import Script from "next/script";
import React, { useEffect, useMemo, useState } from "react";

import { PREVIEW_CONTAINER_ID } from "~/constants";
import { TranslationWithLanguageName } from "~/features/privacy-experience/form/helpers";
import {
  buildBaseConfig,
  generateMockNotices,
  translationOrDefault,
} from "~/features/privacy-experience/preview/helpers";
import theme from "~/theme";
import {
  ComponentType,
  ExperienceConfigCreate,
  Layer1ButtonOption,
  LimitedPrivacyNoticeResponseSchema,
  PrivacyNoticeResponse,
} from "~/types/api";

import { useFeatures } from "../../common/features";
import { COMPONENT_MAP } from "../constants";

declare global {
  interface Window {
    Fides: FidesGlobal;
  }
}

const NoPreviewNotice = ({
  title,
  description,
}: {
  title: string;
  description: string;
}) => (
  <Flex className="h-full items-center justify-center">
    <Flex
      className="items-center gap-2 rounded-md p-6"
      style={{
        backgroundColor: theme.colors.white,
        boxShadow: theme.shadows.md,
        maxWidth: 512,
      }}
      vertical
      data-testid="no-preview-notice"
    >
      <Text fontSize="lg" fontWeight="500" align="center">
        {title}
      </Text>
      <Text color="gray.500" align="center">
        {description}
      </Text>
    </Flex>
  </Flex>
);

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
  const router = useRouter();
  const isNewExperience = router.pathname.includes("/new");
  const { values } = useFormikContext<ExperienceConfigCreate>();
  const [noticesOnConfig, setNoticesOnConfig] = useState<
    PrivacyNoticeResponse[]
  >([]);
  const [fidesScriptLoaded, setFidesScriptLoaded] = useState(false);
  const [previewMode, setPreviewMode] = useState<"standard" | "tcf">();
  const isPreviewAvailable = [
    ComponentType.BANNER_AND_MODAL,
    ComponentType.MODAL,
    ComponentType.TCF_OVERLAY,
  ].includes(values.component);

  const { systemsCount } = useFeatures();

  useEffect(() => {
    if (
      isPreviewAvailable &&
      fidesScriptLoaded &&
      window.FidesPreview &&
      values.component &&
      (values.privacy_notice_ids?.length ||
        values.component === ComponentType.TCF_OVERLAY)
    ) {
      if (values.component === ComponentType.TCF_OVERLAY) {
        window.FidesPreview("tcf");
        setPreviewMode("tcf");
      } else {
        window.FidesPreview("standard");
        setPreviewMode("standard");
      }
    } else if (window.FidesPreview) {
      window.FidesPreview?.cleanup();
    }

    return () => {
      // cleanup fides.js preview when the component unmounts so it doesn't continue to run on other pages
      window.FidesPreview?.cleanup();
    };
  }, [
    values.component,
    fidesScriptLoaded,
    isPreviewAvailable,
    values.privacy_notice_ids?.length,
    isNewExperience,
  ]);

  useEffect(() => {
    if (initialValues && values.component && allPrivacyNotices) {
      if (values.privacy_notice_ids) {
        const notices = generateMockNotices(
          values.privacy_notice_ids,
          values.component,
          allPrivacyNotices,
        );
        setNoticesOnConfig(notices);
      } else {
        setNoticesOnConfig([]);
      }
    }
  }, [
    values.privacy_notice_ids,
    allPrivacyNotices,
    values.component,
    initialValues,
  ]);

  const baseConfig = useMemo(() => {
    return values.component
      ? buildBaseConfig(
          { ...initialValues, component: values.component },
          noticesOnConfig,
        )
      : null;
  }, [initialValues, noticesOnConfig, values.component]);

  useEffect(() => {
    if (
      !isPreviewAvailable ||
      !fidesScriptLoaded ||
      !window.FidesPreview ||
      !window.Fides ||
      (!values.privacy_notice_ids?.length &&
        values.component !== ComponentType.TCF_OVERLAY)
    ) {
      return;
    }
    const updatedConfig = baseConfig;
    // if current component is a modal, we want to force fides.js to show a modal, not a banner component
    if (values.component === ComponentType.MODAL) {
      updatedConfig.experience.experience_config.component =
        ComponentType.MODAL;
    }
    // if we're editing a translation, we want to preview the banner/modal with that language,
    // otherwise we show first translation if exists, else keep default
    const currentTranslation = values.translations?.find(
      (i) => i.language === translation?.language,
    );
    if (values.translations?.length) {
      if (currentTranslation) {
        updatedConfig.experience.available_locales = [
          ...(updatedConfig.experience.available_locales || []),
          currentTranslation.language,
        ];
        updatedConfig.experience.experience_config.translations[0] =
          translationOrDefault(currentTranslation);
        updatedConfig.options.fidesLocale = currentTranslation.language;
      } else if (values.translations) {
        updatedConfig.experience.experience_config.translations[0] =
          translationOrDefault(values.translations[0]);
        updatedConfig.options.fidesLocale = values.translations[0].language;
      }
    }
    updatedConfig.experience.experience_config.show_layer1_notices =
      !!values.privacy_notice_ids?.length && !!values.show_layer1_notices;
    updatedConfig.experience.experience_config.layer1_button_options =
      (values.component === ComponentType.BANNER_AND_MODAL ||
        values.component === ComponentType.TCF_OVERLAY) &&
      values.layer1_button_options
        ? values.layer1_button_options
        : Layer1ButtonOption.OPT_IN_OPT_OUT;
    updatedConfig.options.preventDismissal = !values.dismissable;
    updatedConfig.experience.vendor_count = systemsCount;
    updatedConfig.experience.experience_config.component = values.component;
    // reinitialize fides.js each time the form changes
    window.Fides.init(updatedConfig);

    /**
     * NOTE: as tempting as it may be to just include the full values object in the dependency array,
     * it's not a good idea because it will cause the preview to re-render constantly as the form is updated.
     * Not all form fields require a preview re-render, the fields chosen here are very intentional.
     */
  }, [
    translation,
    baseConfig,
    allPrivacyNotices,
    isPreviewAvailable,
    systemsCount,
    fidesScriptLoaded,
    previewMode,
    values.privacy_notice_ids,
    values.component,
    values.translations,
    values.show_layer1_notices,
    values.layer1_button_options,
    values.dismissable,
    initialValues,
    noticesOnConfig,
  ]);

  const modal = document.getElementById("fides-modal");
  if (modal) {
    modal.removeAttribute("tabindex");
  }

  if (!values.component) {
    return (
      <NoPreviewNotice
        title="No privacy experience type selected"
        description="Please select a privacy experience type to preview."
      />
    );
  }

  if (!isPreviewAvailable) {
    return (
      <NoPreviewNotice
        title={`${COMPONENT_MAP.get(values.component)} preview not available`}
        description={`There is no preview available for ${COMPONENT_MAP.get(values.component)}. You can edit the available settings
    and languages to the left.`}
      />
    );
  }

  if (
    !values.privacy_notice_ids?.length &&
    values.component !== ComponentType.TCF_OVERLAY
  ) {
    return (
      <NoPreviewNotice
        title="No privacy notices added"
        description='To view a preview of this experience, add a privacy notice under
      "Privacy Notices" to the left.'
      />
    );
  }

  return (
    <Flex className="size-full items-center justify-center overflow-scroll">
      {/* style overrides for preview model */}
      <style jsx global>{`
        div#fides-overlay {
          z-index: 5000 !important;
        }
        div#${PREVIEW_CONTAINER_ID} {
          width: 100%;
          padding-top: 45px;
          ${values.component !== ComponentType.TCF_OVERLAY
            ? "padding-bottom: 45px;"
            : ""}
          margin: auto;
          pointer-events: none;
        }
        div#fides-banner-container {
          position: static !important;
          transform: none !important;
          transition: none !important;
        }
        div#fides-banner-container.fides-banner-hidden {
          display: none;
        }
        .fides-modal-container {
          background-color: unset !important;
          position: static !important;
          display: none !important;
        }
        .fides-modal-overlay {
          background-color: inherit !important;
          position: static !important;
          display: none !important;
        }
        div.fides-modal-content {
          position: relative !important;
          transform: none !important;
          left: initial !important;
          top: initial !important;
        }
        div.fides-modal-footer {
          width: unset;
        }
      `}</style>
      {isPreviewAvailable ? (
        <style>
          {`div#fides-modal {
          display: flex !important;
          justify-content: center;
          background-color: unset;
          ${
            values.component === ComponentType.BANNER_AND_MODAL ||
            values.component === ComponentType.TCF_OVERLAY
              ? "padding-bottom: 3rem;"
              : ""
          }
        }`}
        </style>
      ) : null}
      {isMobilePreview ? (
        <style>{`
            div#fides-overlay-wrapper {
              max-width: 400px;
              margin: auto;
            }
            div.fides-modal-button-group {
              flex-direction: column !important;
            }
            div#fides-banner {
              padding: 24px;
              width: 100%;
            }

            div#fides-banner-description {
              margin-bottom: 0px;
            }

            div#fides-banner-inner div#fides-button-group {
              flex-direction: column;
              align-items: flex-start;
              gap: 12px;
              padding-top: 24px;
            }

            .fides-banner-button-group {
              flex-direction: column;
              width: 100%;
            }

            button.fides-banner-button {
              margin: 0px;
              width: 100%;
            }

            div#fides-banner-inner-container {
              display: flex;
              flex-direction: column;
              max-height: 50vh;
              overflow-y: auto;
              scrollbar-gutter: stable;
            }

            div#fides-privacy-policy-link {
              order: 1;
              width: 100%;
            }
            .fides-modal-footer {
              max-width: 100%;
            }
            .fides-banner-secondary-actions {
              flex-direction: column-reverse;
              gap: 12px;
            }
            `}</style>
      ) : (
        <style>{`
              div#fides-banner {
                width: 60%;
              }
            @media (min-width: 768px) {
              div#fides-banner {
                width: 100%;
              }
            }
            @media (min-width: 1155px) {
              div#fides-banner {
                width: 90%;
              }
            }
            @media (min-width: 1440px) {
              div#fides-banner {
                width: 60%;
              }
            }
            `}</style>
      )}
      <Script
        id="fides-js-script"
        src="/api/fides-preview.js"
        onReady={() => {
          setFidesScriptLoaded(true);
        }}
      />
      <div id={PREVIEW_CONTAINER_ID} key={values.component} />
    </Flex>
  );
};

export default Preview;
