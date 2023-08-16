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
  id: number;
  name?: string;
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
  vendors?: Array<EmbeddedVendor>;
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
  id: string; // is this a string or a number?
  name?: string;
  description?: string;
  is_gvl?: boolean;
  purposes?: Array<EmbeddedLineItem>;
  special_purposes?: Array<EmbeddedLineItem>;
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
>;

export type TcStringPreferences = {
    tcf_purposes?: Map<number, TCFPurposeRecord>;
    tcf_special_purposes?: Map<number, TCFPurposeRecord>;
    tcf_vendors?: Map<string, TCFVendorRecord>;
    tcf_features?: Map<number, TCFFeatureRecord>;
    tcf_special_features?: Map<number, TCFFeatureRecord>;
    } | undefined