import type { GVL } from "@iabtechlabtcf/core";
import type {
  PrivacyExperience,
  PrivacyPreferencesRequest,
  UserConsentPreference,
} from "../consent-types";

export enum LegalBasisForProcessingEnum {
  CONSENT = "Consent",
  CONTRACT = "Contract",
  LEGAL_OBLIGATIONS = "Legal obligations",
  VITAL_INTERESTS = "Vital interests",
  PUBLIC_INTEREST = "Public interest",
  LEGITIMATE_INTERESTS = "Legitimate interests",
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
export type TCFConsentVendorRecord = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  consent_purposes?: Array<EmbeddedLineItem>;
};

export type TCFLegitimateInterestsVendorRecord = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  legitimate_interests_purposes?: Array<EmbeddedLineItem>;
};

export type TCFVendorRelationships = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  special_purposes?: Array<EmbeddedLineItem>;
  features?: Array<EmbeddedLineItem>;
  special_features?: Array<EmbeddedLineItem>;
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
  | "tcf_consent_purposes"
  | "tcf_legitimate_interests_purposes"
  | "tcf_special_purposes"
  | "tcf_features"
  | "tcf_special_features"
  | "tcf_consent_vendors"
  | "tcf_legitimate_interests_vendors"
  | "tcf_consent_systems"
  | "tcf_legitimate_interests_systems"
>;

export type TcfModels =
  | TCFPurposeConsentRecord[]
  | TCFPurposeLegitimateInterestsRecord[]
  | TCFSpecialPurposeRecord[]
  | TCFFeatureRecord[]
  | TCFSpecialFeatureRecord[]
  | TCFConsentVendorRecord[]
  | TCFLegitimateInterestsVendorRecord[]
  | undefined;

type TcfCookieKeyConsent = {
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

export type VendorRecord = TCFConsentVendorRecord &
  Pick<TCFLegitimateInterestsVendorRecord, "legitimate_interests_purposes"> &
  TCFVendorRelationships & {
    isFidesSystem: boolean;
    isConsent: boolean;
    isLegint: boolean;
  };

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
export interface GvlVendorUrl {
  langId: string;
  privacy?: string;
  legIntClaim?: string;
}
export interface GvlDataRetention {
  stdRetention: number;
  purposes: Record<number, number>;
  specialPurposes: Record<number, number>;
}
interface GvlDataCategory {
  id: number;
  name: string;
  description: string;
}
export type GvlDataCategories = Record<number, GvlDataCategory>;
export type GvlDataDeclarations = number[];
