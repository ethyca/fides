import { FidesGlobal } from "fides-js/src/lib/consent-types";
import { Flex, Text, useToast } from "fidesui";
import { useFormikContext } from "formik";
import Script from "next/script";
import React, { useEffect, useMemo, useState } from "react";

import { PREVIEW_CONTAINER_ID } from "~/constants";
import { getErrorMessage } from "~/features/common/helpers";
import { Layer1ButtonOption } from "~/features/privacy-experience/form/constants";
import { TranslationWithLanguageName } from "~/features/privacy-experience/form/helpers";
import {
  buildBaseConfig,
  translationOrDefault,
} from "~/features/privacy-experience/preview/helpers";
import { useLazyGetPrivacyNoticeByIdQuery } from "~/features/privacy-notices/privacy-notices.slice";
import {
  ComponentType,
  ExperienceConfigCreate,
  LimitedPrivacyNoticeResponseSchema,
  PrivacyNoticeResponse,
} from "~/types/api";

import PrivacyCenterPreview from "./preview/PrivacyCenterPreview";

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
  <Flex h="full" justify="center" align="center">
    <Flex
      bgColor="white"
      borderRadius="md"
      p={6}
      boxShadow="md"
      direction="column"
      align="center"
      gap="2"
      maxW="512px"
      data-testid="no-preview-notice"
    >
      <Text
        fontSize="lg"
        fontWeight="500"
        align="center"
        id="no-preview-notice-heading"
      >
        {title}
      </Text>
      <Text color="gray.500" align="center" id="no-preview-notice-text">
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
        "A problem occurred while fetching privacy notice data.  Some notices may not display correctly on the preview.",
      );
      toast({ status: "error", description: errorMsg });
    }
    const { data } = await getPrivacyNoticeByIdTrigger(id);
    return data;
  };

  useEffect(() => {
    if (values.privacy_notice_ids) {
      Promise.all(
        values.privacy_notice_ids!.map((id) => getPrivacyNotice(id)),
      ).then((data) =>
        // TS can't tell that we filter out notices that are undefined here
        // @ts-ignore
        setNoticesOnConfig(data.filter((notice) => notice !== undefined)),
      );
    } else {
      setNoticesOnConfig([]);
    }
    // ESLint wants us to have getPrivacyNotice in the dependencies, but doing
    // so makes the privacy notice queries fire on every re-render;
    // we can omit it because it isn't calculated from state or props
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [values.privacy_notice_ids]);

  const fidesJsScript = "/lib/fides.js";

  // Create the base FidesConfig JSON that will be used to initialize fides.js
  const baseConfig = useMemo(
    () => buildBaseConfig(initialValues, noticesOnConfig),
    [initialValues, noticesOnConfig],
  );

  useEffect(() => {
    // if current component is a modal, we want to force fides.js to show a modal, not a banner component
    if (values.component === ComponentType.MODAL) {
      baseConfig.experience.experience_config.component = ComponentType.MODAL;
    }
    // if we're editing a translation, we want to preview the banner/modal with that language,
    // otherwise we show first translation if exists, else keep default
    const currentTranslation = values.translations?.find(
      (i) => i.language === translation?.language,
    );
    if (values.translations?.length) {
      if (currentTranslation) {
        baseConfig.experience.available_locales = [
          ...(baseConfig.experience.available_locales || []),
          currentTranslation.language,
        ];
        baseConfig.experience.experience_config.translations[0] =
          translationOrDefault(currentTranslation);
        baseConfig.options.fidesLocale = currentTranslation.language;
      } else if (values.translations) {
        baseConfig.experience.experience_config.translations[0] =
          translationOrDefault(values.translations[0]);
        baseConfig.options.fidesLocale = values.translations[0].language;
      }
    }
    baseConfig.experience.experience_config.show_layer1_notices =
      !!values.privacy_notice_ids?.length && !!values.show_layer1_notices;
    baseConfig.experience.experience_config.layer1_button_options =
      (values.component === ComponentType.BANNER_AND_MODAL &&
        values.layer1_button_options) ||
      Layer1ButtonOption.OPT_IN_OPT_OUT;
    baseConfig.options.preventDismissal = !values.dismissable;
    if (
      window.Fides &&
      values.privacy_notice_ids?.length &&
      values.component !== ComponentType.PRIVACY_CENTER &&
      values.component !== ComponentType.TCF_OVERLAY
    ) {
      window.Fides.init(baseConfig as any);
    }
  }, [values, translation, baseConfig, allPrivacyNotices]);

  const modal = document.getElementById("fides-modal");
  if (modal) {
    modal.removeAttribute("tabindex");
  }

  if (values.component === ComponentType.TCF_OVERLAY) {
    return (
      <NoPreviewNotice
        title="TCF preview not available"
        description="There is no preview available for TCF. You can edit the available settings
      and languages to the left."
      />
    );
  }

  if (values.component === ComponentType.PRIVACY_CENTER) {
    return <PrivacyCenterPreview stylesheet={values.css} />;
  }

  if (!values.privacy_notice_ids?.length) {
    return (
      <NoPreviewNotice
        title="No privacy notices added"
        description='To view a preview of this experience, add a privacy notice under
      "Privacy Notices" to the left.'
      />
    );
  }

  return (
    <Flex h="full" justify="center" align="center" overflow="scroll">
      {/* style overrides for preview model */}
      <style jsx global>{`
        div#fides-overlay {
          z-index: 5000 !important;
        }
        div#${PREVIEW_CONTAINER_ID} {
          padding-top: 45px;
          margin: auto !important;
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
      {values.component === ComponentType.BANNER_AND_MODAL ||
      values.component === ComponentType.MODAL ? (
        <style>
          {`div#fides-modal {
          display: flex !important;
          justify-content: center;
          background-color: unset;
          ${
            values.component === ComponentType.BANNER_AND_MODAL
              ? "padding-top: 3rem; padding-bottom: 3rem;"
              : ""
          }
        }`}
        </style>
      ) : null}
      {isMobilePreview ? (
        <style>{`
            div#${PREVIEW_CONTAINER_ID} {
              width: 70% !important;
            }
            div.fides-modal-button-group {
              flex-direction: column !important;
            }
            div#fides-modal {
              width: 70% !important;
              margin: auto;
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
              width: 90% !important;
            }
            `}</style>
      )}
      <Script
        id="fides-js-base"
        src={fidesJsScript}
        onReady={() => {
          if (
            values.component !== ComponentType.TCF_OVERLAY &&
            values.component !== ComponentType.PRIVACY_CENTER
          ) {
            window.Fides?.init(baseConfig as any);
          }
        }}
      />
      <div id={PREVIEW_CONTAINER_ID} />
    </Flex>
  );
};

export default Preview;
