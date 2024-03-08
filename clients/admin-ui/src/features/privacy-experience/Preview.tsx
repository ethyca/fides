import { Flex, Text, useToast } from "@fidesui/react";
import {
  CookieKeyConsent,
  EmptyExperience,
  FidesOptions,
  PrivacyExperience,
  UserGeolocation,
} from "fides-js/src/lib/consent-types";
import { useFormikContext } from "formik";
import Script from "next/script";
import React, { useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { TranslationWithLanguageName } from "~/features/privacy-experience/form/helpers";
import {
  buildBaseConfig,
  FidesPreviewComponent,
  translationOrDefault,
} from "~/features/privacy-experience/preview/helpers";
import { useLazyGetPrivacyNoticeByIdQuery } from "~/features/privacy-notices/privacy-notices.slice";
import {
  ComponentType,
  ExperienceConfigCreate,
  LimitedPrivacyNoticeResponseSchema,
  PrivacyNoticeResponse,
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

const NoPreviewNotice = () => (
  <Flex
    bgColor="white"
    borderRadius="md"
    p={6}
    boxShadow="md"
    direction="column"
    align="center"
    gap="2"
    maxW="512px"
  >
    <Text fontSize="lg" fontWeight="500" align="center">
      No privacy notices added
    </Text>
    <Text color="gray.500" align="center">
      To view a preview of this experience, add a privacy notice under
      &quot;Privacy Notices&quot; to the left.
    </Text>
  </Flex>
);

const TCFExperienceNotice = () => (
  <Flex
    bgColor="white"
    borderRadius="md"
    p={6}
    boxShadow="md"
    direction="column"
    align="center"
    gap="2"
    maxW="512px"
  >
    <Text fontSize="lg" fontWeight="500" align="center">
      TCF preview not available
    </Text>
    <Text color="gray.500" align="center">
      There is no preview available for TCF. You can edit the available settings
      and languages to the left.
    </Text>
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
        "A problem occurred while fetching privacy notice data.  Some notices may not display correctly on the preview."
      );
      toast({ status: "error", description: errorMsg });
    }
    const { data } = await getPrivacyNoticeByIdTrigger(id);
    return data;
  };

  useEffect(() => {
    if (values.privacy_notice_ids) {
      Promise.all(
        values.privacy_notice_ids!.map((id) => getPrivacyNotice(id))
      ).then((data) =>
        // TS can't tell that we filter out notices that are undefined here
        // @ts-ignore
        setNoticesOnConfig(data.filter((notice) => notice !== undefined))
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
    [initialValues, noticesOnConfig]
  );

  useEffect(() => {
    // if current component is a modal, we want to force fides.js to show a modal, not a banner component
    if (values.component === ComponentType.MODAL) {
      baseConfig.options.fidesPreviewComponent = FidesPreviewComponent.MODAL;
    }
    // if we're editing a translation, we want to preview the banner/modal with that language,
    // otherwise we show first translation if exists, else keep default
    const currentTranslation = values.translations?.find(
      (i) => i.language === translation?.language
    );
    if (currentTranslation) {
      baseConfig.experience.experience_config.translations[0] =
        translationOrDefault(currentTranslation);
    } else if (values.translations) {
      baseConfig.experience.experience_config.translations[0] =
        translationOrDefault(values.translations[0]);
    }
    baseConfig.options.preventDismissal = !values.dismissable;
    if (window.Fides && values.privacy_notice_ids?.length) {
      window.Fides.init(baseConfig);
    }
  }, [values, translation, baseConfig, allPrivacyNotices]);

  const modal = document.getElementById("fides-modal");
  if (modal) {
    modal.removeAttribute("tabindex");
  }

  if (values.component === ComponentType.TCF_OVERLAY) {
    return (
      <Flex h="full" justify="center" align="center">
        <TCFExperienceNotice />
      </Flex>
    );
  }

  if (!values.privacy_notice_ids?.length) {
    return (
      <Flex h="full" justify="center" align="center">
        <NoPreviewNotice />
      </Flex>
    );
  }

  return (
    <Flex h="full" justify="center" align="center" overflow="scroll">
      {/* style overrides for preview model */}
      <style jsx global>{`
        div#fides-overlay {
          z-index: 5000 !important;
        }
        div#preview-container {
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
        ${values.component === ComponentType.BANNER_AND_MODAL ||
        values.component === ComponentType.MODAL
          ? `div#fides-modal {
          display: flex !important;
          ${
            values.component === ComponentType.BANNER_AND_MODAL
              ? "padding-top: 3rem;"
              : null
          }
          justify-content: center;
          background_color: unset;
        }`
          : null}
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
    </Flex>
  );
};

export default Preview;
