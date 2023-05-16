import { ConsentConfig } from "./consent-config";

export const FIDES_MODAL_LINK = "fides-consent-modal-link";

export interface FidesConfig {
  // Set the consent defaults from a "legacy" Privacy Center config.json.
  consent?: ConsentConfig;
  // Set the "experience" to be used for this Fides.js instance -- overrides the "legacy" config.
  // If set, Fides.js will fetch neither experience config nor user geolocation.
  // If not set, Fides.js will fetch its own experience config.
  experience?: ExperienceConfig;
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

export type ExperienceConfig = {
  version: string;
  component: ExperienceComponent;
  delivery_mechanism: ExperienceDeliveryMechanism;
  regions: Array<string>;
  component_title: string;
  component_description: string;
  banner_title: string;
  banner_description: string;
  confirmation_button_label: string;
  reject_button_label: string;
  privacy_notices: Array<PrivacyNotice>;
};

export type PrivacyNotice = {
  name: string;
  description?: string;
  regions: Array<string>;
  consent_mechanism: ConsentMechanism;
  default_preference: ConsentPreference;
  current_preference: ConsentPreference | null;
  outdated_preference: ConsentPreference | null;
  has_gpc_flag: boolean;
  data_uses: Array<string>;
  enforcement_level: EnforcementLevel;
  displayed_in_overlay?: boolean;
  displayed_in_api?: boolean;
  displayed_in_privacy_center?: boolean;
  id: string;
  created_at: string;
  updated_at: string;
  version: number;
  privacy_notice_history_id: string;
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

export enum ConsentPreference {
  OPT_IN = "opt_in",
  OPT_OUT = "opt_out",
}

export enum ExperienceComponent {
  OVERLAY = "overlay",
  PRIVACY_CENTER = "privacy_center",
}

export enum ExperienceDeliveryMechanism {
  BANNER = "banner",
  LINK = "link",
  API = "api",
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
