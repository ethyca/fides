import * as Yup from "yup";

import { getOptionsFromMap } from "~/features/common/utils";
import {
  ENFORCEMENT_LEVEL_MAP,
  MECHANISM_MAP,
} from "~/features/privacy-notices/constants";
import {
  ConsentMechanism,
  EnforcementLevel,
  NoticeTranslationCreate,
  PrivacyNoticeCreation,
  PrivacyNoticeResponse,
  SupportedLanguage,
} from "~/types/api";

interface PrivacyNoticeUpdateOrCreate extends PrivacyNoticeCreation {
  id?: string;
}

export const CONSENT_MECHANISM_OPTIONS = getOptionsFromMap(MECHANISM_MAP);

export const ENFORCEMENT_LEVEL_OPTIONS = getOptionsFromMap(
  ENFORCEMENT_LEVEL_MAP,
);

export const defaultInitialTranslations: NoticeTranslationCreate[] = [
  {
    language: SupportedLanguage.EN,
    title: "",
    description: "",
  },
];

export const defaultInitialValues: PrivacyNoticeUpdateOrCreate = {
  name: "",
  consent_mechanism: ConsentMechanism.OPT_IN,
  data_uses: [],
  enforcement_level: EnforcementLevel.FRONTEND,
  // When creating, set to disabled to start
  disabled: true,
  translations: defaultInitialTranslations,
  children: [],
};

export const transformPrivacyNoticeResponseToCreation = (
  notice: PrivacyNoticeResponse,
): PrivacyNoticeUpdateOrCreate => ({
  name: notice.name ?? defaultInitialValues.name,
  consent_mechanism:
    notice.consent_mechanism ?? defaultInitialValues.consent_mechanism,
  data_uses: notice.data_uses ?? defaultInitialValues.data_uses,
  enforcement_level:
    notice.enforcement_level ?? defaultInitialValues.enforcement_level,
  notice_key: notice.notice_key,
  disabled: notice.disabled,
  has_gpc_flag: notice.has_gpc_flag,
  id: notice.id,
  internal_description: notice.internal_description,
  translations: notice.translations
    ? notice.translations.map((t) => {
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { privacy_notice_history_id, ...rest } = t;
        return {
          ...rest,
          title: t.title ?? "",
        };
      })
    : defaultInitialTranslations,
  children: notice.children,
});

export const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Title"),
  consent_mechanism: Yup.string().required().label("Consent mechanism"),
});
