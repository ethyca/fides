import * as Yup from "yup";

import {
  ConsentMechanism,
  EnforcementLevel,
  PrivacyNoticeCreation,
  PrivacyNoticeResponse,
  SupportedLanguage,
} from "~/types/api";

interface PrivacyNoticeUpdateOrCreate extends PrivacyNoticeCreation {
  id?: string;
}

export const CONSENT_MECHANISM_OPTIONS = [
  {
    label: "Opt in",
    value: ConsentMechanism.OPT_IN,
  },
  {
    label: "Opt out",
    value: ConsentMechanism.OPT_OUT,
  },
  {
    label: "Notice only",
    value: ConsentMechanism.NOTICE_ONLY,
  },
];

export const defaultInitialValues: PrivacyNoticeUpdateOrCreate = {
  name: "",
  consent_mechanism: ConsentMechanism.OPT_IN,
  data_uses: [],
  enforcement_level: EnforcementLevel.SYSTEM_WIDE,
  // When creating, set to disabled to start
  disabled: true,
  translations: [
    {
      language: SupportedLanguage.EN,
      title: "",
    },
  ],
};

export const transformPrivacyNoticeResponseToCreation = (
  notice: PrivacyNoticeResponse
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
  translations: notice.translations ? notice.translations.map((t) => ({
    
  }))
});

export const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Title"),
});
