import {
  ExperienceConfig,
  PrivacyNotice,
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
} from "fides-js";
import { useCallback, useContext } from "react";

import { ExperienceConfigResponseNoNotices } from "~/types/api";

import { I18nContext } from "../i18nContext";

const useI18n = () => {
  const context = useContext(I18nContext);
  const i18n = context.i18nInstance;

  if (!context) {
    throw new Error("useI18n must be used within a I18nProvider");
  }

  // Useful wrapper for selectBestExperienceConfigTranslation
  const selectExperienceConfigTranslation = useCallback(
    (
      experienceConfig:
        | ExperienceConfig
        | ExperienceConfigResponseNoNotices
        | undefined,
    ) => {
      if (!experienceConfig) {
        throw new Error("ExperienceConfig must be defined");
      }

      const experienceConfigTransalation =
        selectBestExperienceConfigTranslation(
          i18n,
          // DEFER (PROD-2737) remove type casting
          experienceConfig as ExperienceConfig,
        );

      if (!experienceConfigTransalation) {
        throw new Error("Coudln't find correct experience config translation");
      }

      return experienceConfigTransalation;
    },
    [i18n],
  );

  // Useful wrapper for selectBestNoticeTranslation
  const selectNoticeTranslation = useCallback(
    (notice: PrivacyNotice) => {
      const selectedNotice = selectBestNoticeTranslation(
        i18n,
        notice as PrivacyNotice,
      );
      if (!selectedNotice) {
        throw new Error("Coudln't find correct notice translation");
      }
      return selectedNotice;
    },
    [i18n],
  );

  return {
    ...context,
    i18n,
    selectExperienceConfigTranslation,
    selectNoticeTranslation,
  };
};
export default useI18n;
