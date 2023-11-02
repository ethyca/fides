import type { GVL } from "@iabtechlabtcf/core";
import type {
  PrivacyExperience,
  PrivacyPreferencesRequest,
  UserConsentPreference,
} from "../consent-types";

enum LegalBasisForProcessingEnum {
  CONSENT = "Consent",
  CONTRACT = "Contract",
  LEGAL_OBLIGATIONS = "Legal obligations",
  VITAL_INTERESTS = "Vital interests",
  PUBLIC_INTEREST = "Public interest",
  LEGITIMATE_INTERESTS = "Legitimate interests",
}

// These are the only relevant ones for TCF
export enum LegalBasisEnum {
  CONSENT = LegalBasisForProcessingEnum.CONSENT,
  LEGITIMATE_INTERESTS = LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS,
}

// Embedded items
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
  retention_period?: string;
};

// Purposes
export type TCFPurposeConsentRecord = {
  id: number;
  name: string;
  description: string;
  illustrations: Array<string>;
  data_uses: Array<string>;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};

export type TCFPurposeLegitimateInterestsRecord = {
  id: number;
  name: string;
  description: string;
  illustrations: Array<string>;
  data_uses: Array<string>;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};

export type TCFPurposeSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

// Special purposes
export type TCFSpecialPurposeRecord = {
  id: number;
  name: string;
  description: string;
  illustrations: Array<string>;
  data_uses: Array<string>;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};

export type TCFSpecialPurposeSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

// Features
export type TCFFeatureRecord = {
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  id: number;
  name: string;
  description: string;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};

export type TCFFeatureSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

// Special features
export type TCFSpecialFeatureRecord = {
  id: number;
  name: string;
  description: string;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};

export type TCFSpecialFeatureSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

// Vendor records
export type TCFVendorConsentRecord = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  purpose_consents?: Array<EmbeddedPurpose>;
};

export type TCFVendorLegitimateInterestsRecord = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  purpose_legitimate_interests?: Array<EmbeddedPurpose>;
};

export type TCFVendorRelationships = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  special_purposes?: Array<EmbeddedPurpose>;
  features?: Array<EmbeddedLineItem>;
  special_features?: Array<EmbeddedLineItem>;
  cookie_max_age_seconds?: number;
  uses_cookies?: boolean;
  cookie_refresh?: boolean;
  uses_non_cookie_access?: boolean;
  legitimate_interest_disclosure_url?: string;
  privacy_policy_url?: string;
};

export type TCFVendorSave = {
  id: string;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

// Convenience types, frontend only
export type TcfSavePreferences = Pick<
  PrivacyPreferencesRequest,
  | "purpose_consent_preferences"
  | "purpose_legitimate_interests_preferences"
  | "special_feature_preferences"
  | "vendor_consent_preferences"
  | "vendor_legitimate_interests_preferences"
  | "system_consent_preferences"
  | "system_legitimate_interests_preferences"
>;

export type TcfExperienceRecords = Pick<
  PrivacyExperience,
  | "tcf_purpose_consents"
  | "tcf_purpose_legitimate_interests"
  | "tcf_special_purposes"
  | "tcf_features"
  | "tcf_special_features"
  | "tcf_vendor_consents"
  | "tcf_vendor_legitimate_interests"
  | "tcf_system_consents"
  | "tcf_system_legitimate_interests"
>;

export type TcfModels =
  | TCFPurposeConsentRecord[]
  | TCFPurposeLegitimateInterestsRecord[]
  | TCFSpecialPurposeRecord[]
  | TCFFeatureRecord[]
  | TCFSpecialFeatureRecord[]
  | TCFVendorConsentRecord[]
  | TCFVendorLegitimateInterestsRecord[]
  | undefined;

export type TcfModelsRecord =
  | TCFPurposeConsentRecord
  | TCFPurposeLegitimateInterestsRecord
  | TCFSpecialPurposeRecord
  | TCFFeatureRecord
  | TCFSpecialFeatureRecord
  | TCFVendorConsentRecord
  | TCFVendorLegitimateInterestsRecord;

export type TcfCookieKeyConsent = {
  [id: string | number]: boolean | undefined;
};

export interface TcfCookieConsent {
  purpose_consent_preferences?: TcfCookieKeyConsent;
  purpose_legitimate_interests_preferences?: TcfCookieKeyConsent;
  special_feature_preferences?: TcfCookieKeyConsent;
  vendor_consent_preferences?: TcfCookieKeyConsent;
  vendor_legitimate_interests_preferences?: TcfCookieKeyConsent;
  system_consent_preferences?: TcfCookieKeyConsent;
  system_legitimate_interests_preferences?: TcfCookieKeyConsent;
}

export type TcfModelType = keyof TcfCookieConsent;

export interface EnabledIds {
  purposesConsent: string[];
  purposesLegint: string[];
  specialPurposes: string[];
  features: string[];
  specialFeatures: string[];
  vendorsConsent: string[];
  vendorsLegint: string[];
}

export type VendorRecord = TCFVendorConsentRecord &
  Pick<TCFVendorLegitimateInterestsRecord, "purpose_legitimate_interests"> &
  TCFVendorRelationships & {
    isFidesSystem: boolean;
    isConsent: boolean;
    isLegint: boolean;
    isGvl: boolean;
  };

export interface PurposeRecord extends TCFPurposeConsentRecord {
  isConsent: boolean;
  isLegint: boolean;
}

export type GVLJson = Pick<
  GVL,
  | "gvlSpecificationVersion"
  | "vendorListVersion"
  | "tcfPolicyVersion"
  | "lastUpdated"
  | "stacks"
  | "purposes"
  | "specialPurposes"
  | "features"
  | "specialFeatures"
  | "vendors"
>;

// GVL types—we should be able to get these from the library at some point,
// but since they are on GVL 2.2, the types aren't quite right for GVL 3.
interface GvlDataCategory {
  id: number;
  name: string;
  description: string;
}
export type GvlDataCategories = Record<number, GvlDataCategory>;
export type GvlDataDeclarations = number[];
