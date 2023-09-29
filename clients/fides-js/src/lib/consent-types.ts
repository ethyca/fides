import type {
  TCFPurposeRecord,
  TCFVendorRecord,
  TCFFeatureRecord,
  TCFPurposeSave,
  TCFSpecialPurposeSave,
  TCFFeatureSave,
  TCFSpecialFeatureSave,
  TCFVendorSave,
  GVLJson,
} from "./tcf/types";

export type EmptyExperience = Record<PropertyKey, never>;

export interface FidesConfig {
  // Set the consent defaults from a "legacy" Privacy Center config.json.
  consent?: LegacyConsentConfig;
  // Set the "experience" to be used for this Fides.js instance -- overrides the "legacy" config.
  // If defined or is empty, Fides.js will not fetch experience config.
  // If undefined, Fides.js will attempt to fetch its own experience config.
  experience?: PrivacyExperience | EmptyExperience;
  // Set the geolocation for this Fides.js instance. If *not* set, Fides.js will fetch its own geolocation.
  geolocation?: UserGeolocation;
  // Global options for this Fides.js instance. Fides provides defaults for all props except privacyCenterUrl
  options: FidesOptions;
}

export type FidesOptions = {
  // Whether or not debug log statements should be enabled
  debug: boolean;

  // API URL for getting user geolocation
  geolocationApiUrl: string;

  // Whether or not the banner should be globally enabled
  isOverlayEnabled: boolean;

  // Whether we should pre-fetch geolocation and experience server-side
  isPrefetchEnabled: boolean;

  // Whether user geolocation should be enabled. Requires geolocationApiUrl
  isGeolocationEnabled: boolean;

  // ID of the parent DOM element where the overlay should be inserted (default: "fides-overlay")
  overlayParentId: string | null;

  // ID of the DOM element that should trigger the consent modal (default: "fides-modal-link"
  modalLinkId: string | null;

  // URL for the Privacy Center, used to customize consent preferences. Required.
  privacyCenterUrl: string;

  // URL for the Fides API, used to fetch and save consent preferences. Required.
  fidesApiUrl: string;

  // URL for Server-side Fides API, used to fetch geolocation and consent preference. Optional.
  serverSideFidesApiUrl: string;

  // Whether we should show the TCF modal
  tcfEnabled?: boolean;
};

export class SaveConsentPreference {
  consentPreference: UserConsentPreference;

  notice: PrivacyNotice;

  constructor(notice: PrivacyNotice, consentPreference: UserConsentPreference) {
    this.notice = notice;
    this.consentPreference = consentPreference;
  }
}

export type PrivacyExperience = {
  region: string; // intentionally using plain string instead of Enum, since BE is susceptible to change
  component?: ComponentType;
  experience_config?: ExperienceConfig;
  id: string;
  created_at: string;
  updated_at: string;
  show_banner?: boolean;
  privacy_notices?: Array<PrivacyNotice>;
  tcf_purposes?: Array<TCFPurposeRecord>;
  tcf_special_purposes?: Array<TCFPurposeRecord>;
  tcf_vendors?: Array<TCFVendorRecord>;
  tcf_systems?: Array<TCFVendorRecord>;
  tcf_features?: Array<TCFFeatureRecord>;
  tcf_special_features?: Array<TCFFeatureRecord>;
  gvl?: GVLJson;
};

export type ExperienceConfig = {
  accept_button_label?: string;
  acknowledge_button_label?: string;
  banner_enabled?: BannerEnabled;
  description?: string;
  disabled?: boolean;
  is_default?: boolean;
  privacy_policy_link_label?: string;
  privacy_policy_url?: string;
  privacy_preferences_link_label?: string;
  reject_button_label?: string;
  save_button_label?: string;
  title?: string;
  id: string;
  component: ComponentType;
  experience_config_history_id: string;
  version: number;
  created_at: string;
  updated_at: string;
  regions: Array<string>;
};

export type Cookies = {
  name: string;
  path?: string;
  domain?: string;
};

export type PrivacyNotice = {
  name?: string;
  notice_key: string;
  description?: string;
  internal_description?: string;
  origin?: string;
  regions?: Array<string>;
  consent_mechanism?: ConsentMechanism;
  data_uses?: Array<string>;
  enforcement_level?: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  displayed_in_privacy_center?: boolean;
  displayed_in_overlay?: boolean;
  displayed_in_api?: boolean;
  id: string;
  created_at: string;
  updated_at: string;
  version: number;
  privacy_notice_history_id: string;
  cookies: Array<Cookies>;
  default_preference: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
};

export enum EnforcementLevel {
  FRONTEND = "frontend",
  SYSTEM_WIDE = "system_wide",
  NOT_APPLICABLE = "not_applicable",
}

export enum ConsentMechanism {
  OPT_IN = "opt_in",
  OPT_OUT = "opt_out",
  NOTICE_ONLY = "notice_only",
}

export enum UserConsentPreference {
  OPT_IN = "opt_in",
  OPT_OUT = "opt_out",
  ACKNOWLEDGE = "acknowledge",
}

export enum ComponentType {
  OVERLAY = "overlay",
  PRIVACY_CENTER = "privacy_center",
  TCF_OVERLAY = "tcf_overlay",
}

export enum BannerEnabled {
  ALWAYS_ENABLED = "always_enabled",
  ENABLED_WHERE_REQUIRED = "enabled_where_required",
  ALWAYS_DISABLED = "always_disabled",
}

export type UserGeolocation = {
  country?: string; // "US"
  ip?: string; // "192.168.0.1:12345"
  location?: string; // "US-NY"
  region?: string; // "NY"
};

// Regex to validate a location string, which must:
// 1) Start with a 2-3 character country code (e.g. "US")
// 2) Optionally end with a 2-3 character region code (e.g. "CA")
// 3) Separated by a dash (e.g. "US-CA")
export const VALID_ISO_3166_LOCATION_REGEX = /^\w{2,3}(-\w{2,3})?$/;

export enum ButtonType {
  PRIMARY = "primary",
  SECONDARY = "secondary",
  TERTIARY = "tertiary",
}

export enum ConsentMethod {
  button = "button",
  gpc = "gpc",
  individual_notice = "api",
}

export type PrivacyPreferencesRequest = {
  browser_identity: Identity;
  code?: string;
  preferences?: Array<ConsentOptionCreate>;
  purpose_preferences?: Array<TCFPurposeSave>;
  special_purpose_preferences?: Array<TCFSpecialPurposeSave>;
  vendor_preferences?: Array<TCFVendorSave>;
  system_preferences?: Array<TCFVendorSave>;
  feature_preferences?: Array<TCFFeatureSave>;
  special_feature_preferences?: Array<TCFSpecialFeatureSave>;
  policy_key?: string; // Will use default consent policy if not supplied
  privacy_experience_id?: string;
  user_geography?: string;
  method?: ConsentMethod;
};

export type ConsentOptionCreate = {
  privacy_notice_history_id: string;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};

export type Identity = {
  phone_number?: string;
  email?: string;
  ga_client_id?: string;
  ljt_readerID?: string;
  fides_user_device_id?: string;
};

export enum RequestOrigin {
  privacy_center = "privacy_center",
  overlay = "overlay",
  api = "api",
}

export enum GpcStatus {
  /** GPC is not relevant for the consent option. */
  NONE = "none",
  /** GPC is enabled and consent matches the configured default. */
  APPLIED = "applied",
  /** GPC is enabled but consent has been set to override the configured default. */
  OVERRIDDEN = "overridden",
}

// Consent reporting
export enum ServingComponent {
  OVERLAY = "overlay",
  BANNER = "banner",
  PRIVACY_CENTER = "privacy_center",
  TCF_OVERLAY = "tcf_overlay",
}
/**
 * Request body when indicating that notices were served in the UI
 */
export type NoticesServedRequest = {
  browser_identity: Identity;
  code?: string;
  privacy_notice_history_ids: Array<string>;
  privacy_experience_id?: string;
  user_geography?: string;
  acknowledge_mode?: boolean;
  serving_component: ServingComponent;
};
/**
 * Schema that surfaces the last version of a notice that was shown to a user
 */
export type LastServedNoticeSchema = {
  id: string;
  updated_at: string;
  privacy_notice_history: PrivacyNotice;
  served_notice_history_id: string;
};

// ------------------LEGACY TYPES BELOW -------------------

export type ConditionalValue = {
  value: boolean;
  globalPrivacyControl: boolean;
};

/**
 * A consent value can be a boolean:
 *  - `true`: consent/opt-in
 *  - `false`: revoke/opt-out
 *
 * A consent value can also be context-dependent, which means it will be decided based on
 * information about the user's environment (browser). The `ConditionalValue` object maps the
 * context conditions to the value that should be used:
 *  - `value`: The default value if no context applies.
 *  - `globalPrivacyControl`: The value to use if the user's browser has Global Privacy Control
 *    enabled.
 */
export type ConsentValue = boolean | ConditionalValue;

export type ConsentOption = {
  cookieKeys: string[];
  default?: ConsentValue;
  fidesDataUseKey: string;
};

export type LegacyConsentConfig = {
  options: ConsentOption[];
};
