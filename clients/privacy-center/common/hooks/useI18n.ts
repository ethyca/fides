import { useContext } from "react";
import {
  ExperienceConfig,
  PrivacyNotice,
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
} from "fides-js";
import { I18nContext } from "../i18nContext";

const useI18n = () => {
  const context = useContext(I18nContext);
  const i18n = context.i18nInstance;

  if (!context) {
    throw new Error("useI18n must be used within a I18nProvider");
  }

  const getPrivacyExperienceConfigHistoryId = (
    experienceConfig: ExperienceConfig
  ) => {
    const experienceConfigTransalation = selectBestExperienceConfigTranslation(
      i18n,
      experienceConfig
    );
    if (!experienceConfigTransalation) {
      throw new Error(
        "Coudln't find correct privacy experience config history id to save consent"
      );
    }

    const privacyExperienceConfigHistoryId =
      experienceConfigTransalation.privacy_experience_config_history_id;

    return privacyExperienceConfigHistoryId;
  };

  const getPrivacyExperienceNoticeHistoryId = (notice: PrivacyNotice) => {
    const selectedNotice = selectBestNoticeTranslation(
      i18n,
      notice as PrivacyNotice
    );
    if (!selectedNotice) {
      throw new Error(
        "Coudln't find correct privacy experience notice history id to save consent"
      );
    }

    const privacyExperienceConfigNoticeId =
      selectedNotice?.privacy_notice_history_id;

    return privacyExperienceConfigNoticeId;
  };

  return {
    ...context,
    i18n,
    getPrivacyExperienceConfigHistoryId,
    getPrivacyExperienceNoticeHistoryId,
  };
};
export default useI18n;
