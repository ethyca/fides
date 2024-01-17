import localeCodes from "locale-codes";
import * as Yup from "yup";

import { Option } from "~/features/common/form/inputs";
import {
  ConsentMechanism,
  EnforcementLevel,
  PrivacyNoticeCreation,
  PrivacyNoticeRegion,
  PrivacyNoticeResponse,
} from "~/types/api";

interface PrivacyNoticeUpdateOrCreate extends PrivacyNoticeCreation {
  id?: string;
}

// TEMP
export type NewPrivacyNotice = {
  name?: string;
  consent_mechanism?: ConsentMechanism;
  data_uses?: string[];
  disabled?: boolean;
  enforcement_level?: EnforcementLevel;
  has_gpc_flag?: boolean;
  internal_description?: string;
  regions?: PrivacyNoticeRegion[];
  notice_key?: string;
  translations: NoticeTranslation[];
};

// TEMP
export type NoticeTranslation = {
  language: string;
  title: string;
  description: string;
};

// TEMP
const DEFAULT_TRANSLATION = {
  language: "en-US",
  title: "",
  description: "",
};

export const getLanguageNameByTag = (tag: string): string => {
  const localeInfo = localeCodes.getByTag(tag);
  return localeInfo.location
    ? `${localeInfo.name} (${localeInfo.location})`
    : localeInfo.name;
};

export const getLanguageOptionByTag = (tag: string): Option => ({
  value: tag,
  label: getLanguageNameByTag(tag),
});

// TEMP
export const newDefaultInitialValues: NewPrivacyNotice = {
  name: "",
  regions: [],
  consent_mechanism: ConsentMechanism.OPT_IN,
  data_uses: [],
  enforcement_level: EnforcementLevel.SYSTEM_WIDE,
  translations: [DEFAULT_TRANSLATION],
};

export type NewPrivacyNoticeCreation = {
  name: string;
  notice_key?: string;
  description?: string;
  internal_description?: string;
  origin?: string;
  regions: Array<PrivacyNoticeRegion>;
  consent_mechanism: ConsentMechanism;
  data_uses: Array<string>;
  enforcement_level: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  displayed_in_privacy_center?: boolean;
  displayed_in_overlay?: boolean;
  displayed_in_api?: boolean;
  translations: NoticeTranslation[];
};

interface NewPrivacyNoticeUpdateOrCreate extends NewPrivacyNoticeCreation {
  id?: string;
}

export const defaultInitialValues: PrivacyNoticeUpdateOrCreate = {
  name: "",
  regions: [],
  consent_mechanism: ConsentMechanism.OPT_IN,
  data_uses: [],
  enforcement_level: EnforcementLevel.SYSTEM_WIDE,
  // Match backend defaults
  displayed_in_api: true,
  displayed_in_overlay: true,
  displayed_in_privacy_center: true,
};

export const transformPrivacyNoticeResponseToCreation = (
  notice: PrivacyNoticeResponse
): PrivacyNoticeUpdateOrCreate => ({
  name: notice.name ?? defaultInitialValues.name,
  regions: notice.regions ?? defaultInitialValues.regions,
  consent_mechanism:
    notice.consent_mechanism ?? defaultInitialValues.consent_mechanism,
  data_uses: notice.data_uses ?? defaultInitialValues.data_uses,
  enforcement_level:
    notice.enforcement_level ?? defaultInitialValues.enforcement_level,
  displayed_in_api: notice.displayed_in_api,
  displayed_in_overlay: notice.displayed_in_overlay,
  displayed_in_privacy_center: notice.displayed_in_privacy_center,
  notice_key: notice.notice_key,
  description: notice.description,
  disabled: notice.disabled,
  has_gpc_flag: notice.has_gpc_flag,
  id: notice.id,
  internal_description: notice.internal_description,
  origin: notice.origin,
});

export const transformNewPrivacyNoticeResponseToCreation = (
  notice: NewPrivacyNotice
): NewPrivacyNoticeUpdateOrCreate => ({
  name: notice.name ?? newDefaultInitialValues.name!,
  regions: notice.regions ?? newDefaultInitialValues.regions!,
  consent_mechanism:
    notice.consent_mechanism ?? newDefaultInitialValues.consent_mechanism!,
  data_uses: notice.data_uses ?? newDefaultInitialValues.data_uses!,
  enforcement_level:
    notice.enforcement_level ?? newDefaultInitialValues.enforcement_level!,
  translations: notice.translations ?? newDefaultInitialValues.translations,
  notice_key: notice.notice_key,
  disabled: notice.disabled,
  has_gpc_flag: notice.has_gpc_flag,
  internal_description: notice.internal_description,
});

export const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Title"),
  data_uses: Yup.array(Yup.string())
    .min(1, "Must assign at least one data use")
    .label("Data uses"),
  regions: Yup.array(Yup.string())
    .min(1, "Must assign at least one location")
    .label("Locations"),
});
