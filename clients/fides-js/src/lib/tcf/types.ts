import type {
  PrivacyExperience,
  PrivacyPreferencesRequest,
  UserConsentPreference,
} from "../consent-types";

export type EmbeddedLineItem = {
  id: number;
  name: string;
};

export type EmbeddedVendor = {
  id: string;
  name: string;
};

export type EmbeddedPurpose = {
  id: number;
  name: string;
  legal_bases?: Array<string>;
};

export type TCFDataCategoryRecord = {
  id: string;
  name?: string;
  cookie?: string;
  domain?: string;
  duration?: string;
};

export type TCFFeatureRecord = {
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  /**
   * Official GVL feature ID or special feature ID
   */
  id: number;
  /**
   * Name of the GVL feature or special feature.
   */
  name: string;
  /**
   * Description of the GVL feature or special feature.
   */
  description: string;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};

export type TCFFeatureSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

export type TCFPurposeRecord = {
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  /**
   * Official GVL purpose ID. Used for linking with other records, e.g. vendors, cookies, etc.
   */
  id: number;
  /**
   * Name of the GVL purpose.
   */
  name: string;
  /**
   * Description of the GVL purpose.
   */
  description: string;
  /**
   * Illustrative examples of the purpose.
   */
  illustrations: Array<string>;
  /**
   * The fideslang default taxonomy data uses that are associated with the purpose.
   */
  data_uses: Array<string>;
  legal_bases?: Array<string>;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};

export type TCFPurposeSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

export type TCFSpecialFeatureSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

export type TCFSpecialPurposeSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

export type TCFVendorRecord = {
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  id: string;
  has_vendor_id: boolean;
  name?: string;
  description?: string;
  purposes?: Array<EmbeddedPurpose>;
  special_purposes?: Array<EmbeddedPurpose>;
  data_categories?: Array<TCFDataCategoryRecord>;
  features?: Array<EmbeddedLineItem>;
  special_features?: Array<EmbeddedLineItem>;
};

export type TCFVendorSave = {
  id: string;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

export type TcfSavePreferences = Pick<
  PrivacyPreferencesRequest,
  | "purpose_preferences"
  | "special_purpose_preferences"
  | "feature_preferences"
  | "special_feature_preferences"
  | "vendor_preferences"
  | "system_preferences"
>;

export type TcfExperienceRecords = Pick<
  PrivacyExperience,
  | "tcf_purposes"
  | "tcf_special_purposes"
  | "tcf_features"
  | "tcf_special_features"
  | "tcf_vendors"
  | "tcf_systems"
>;

type TcfCookieKeyConsent = {
  [id: string | number]: boolean | undefined;
};

export interface TcfCookieConsent {
  purpose_preferences?: TcfCookieKeyConsent;
  special_purpose_preferences?: TcfCookieKeyConsent;
  feature_preferences?: TcfCookieKeyConsent;
  special_feature_preferences?: TcfCookieKeyConsent;
  vendor_preferences?: TcfCookieKeyConsent;
  system_preferences?: TcfCookieKeyConsent;
}

export type TcfModelType = keyof TcfCookieConsent;

export enum LegalBasisForProcessingEnum {
  CONSENT = "Consent",
  CONTRACT = "Contract",
  LEGAL_OBLIGATIONS = "Legal obligations",
  VITAL_INTERESTS = "Vital interests",
  PUBLIC_INTEREST = "Public interest",
  LEGITIMATE_INTERESTS = "Legitimate interests",
}
