import { ConsentConfig } from "./consent-config";

export const FIDES_MODAL_LINK = "fides-consent-modal-link";

export interface FidesConfig {
  // Set the consent defaults from a "legacy" Privacy Center config.json.
  consent?: ConsentConfig;
  // Set the "experience" to be used for this Fides.js instance -- overrides the "legacy" config.
  // If set, Fides.js will fetch neither experience config nor user geolocation.
  // If not set, Fides.js will fetch its own experience config.
  experience?: PrivacyExperience;
  // Set the geolocation for this Fides.js instance. If *not* set, Fides.js will fetch its own geolocation.
  geolocation?: UserGeolocation;
  // Global options for this Fides.js instance. Fides provides defaults for all props except privacyCenterUrl
  options: FidesOptions;
}

export type FidesOptions = {
  // Whether or not debug log statements should be enabled
  debug: boolean;

  // Whether or not the banner should be globally disabled
  isOverlayDisabled: boolean;

  // Whether user geolocation should be enabled. Requires geolocationApiUrl
  isGeolocationEnabled: boolean;

  // API URL for getting user geolocation
  geolocationApiUrl: string;

  // URL for the Privacy Center, used to customize consent preferences. Required.
  privacyCenterUrl: string;
};

export type PrivacyExperience = {
  disabled?: boolean;
  component?: ComponentType;
  delivery_mechanism?: DeliveryMechanism;
  region: string; // intentionally using plain string instead of Enum, since BE is susceptible to change
  experience_config?: ExperienceConfig;
  id: string;
  created_at: string;
  updated_at: string;
  version: number;
  privacy_experience_history_id: string;
  privacy_notices?: Array<PrivacyNotice>;
};

export type ExperienceConfig = {
  acknowledgement_button_label?: string;
  banner_title?: string;
  banner_description?: string;
  component?: ComponentType;
  component_title?: string;
  component_description?: string;
  confirmation_button_label?: string;
  delivery_mechanism?: DeliveryMechanism;
  disabled?: boolean;
  is_default?: boolean;
  link_label?: string;
  reject_button_label?: string;
  id: string;
  experience_config_history_id: string;
  version: number;
  created_at: string;
  updated_at: string;
  regions: Array<string>;
}

export type PrivacyNotice = {
  name?: string;
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
}

export enum DeliveryMechanism {
  BANNER = "banner",
  LINK = "link",
}

export type UserGeolocation = {
  country?: string; // "US"
  ip?: string; // "192.168.0.1:12345"
  location?: string; // "US-NY"
  region?: string; // "NY"
};

export enum ButtonType {
  PRIMARY = "primary",
  SECONDARY = "secondary",
  TERTIARY = "tertiary",
}

export type PrivacyPreferencesCreateWithCode = {
  // TODO: update this schema
  browser_identity: Identity;
  code?: string;
  preferences: Array<ConsentOptionCreate>;
  policy_key?: string;  // Will use default consent policy if not supplied
  request_origin?: RequestOrigin;
  url_recorded?: string;
  user_agent?: string;
  user_geography?: string;
}

export type ConsentOptionCreate = {
  privacy_notice_history_id: string
  preference: UserConsentPreference
}

export type Identity = {
  phone_number?: string;
  email?: string;
  ga_client_id?: string;
  ljt_readerID?: string;
  fides_user_device_id?: string;
}

export enum RequestOrigin {
  privacy_center = "privacy_center",
  overlay = "overlay",
  api = "api"
}
