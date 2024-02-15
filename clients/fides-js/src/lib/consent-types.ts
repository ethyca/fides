import type { GPPFieldMapping, GPPSettings } from "./gpp/types";
import type {
  GVLJson,
  TCFFeatureRecord,
  TCFFeatureSave,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFPurposeSave,
  TCFSpecialFeatureRecord,
  TCFSpecialFeatureSave,
  TCFSpecialPurposeRecord,
  TCFSpecialPurposeSave,
  TCFVendorConsentRecord,
  TCFVendorLegitimateInterestsRecord,
  TCFVendorRelationships,
  TCFVendorSave,
} from "./tcf/types";
import { TcfCookieConsent } from "./tcf/types";

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
  tcfEnabled: boolean;

  // Whether we should "embed" the fides.js overlay UI (ie. “Layer 2”) into a web page instead of as a pop-up
  // overlay, and never render the banner (ie. “Layer 1”).
  fidesEmbed: boolean;

  // Whether we should disable saving consent preferences to the Fides API.
  fidesDisableSaveApi: boolean;

  // Whether we should disable the banner
  fidesDisableBanner: boolean;

  // An explicitly passed-in TC string that supersedes the cookie, and prevents any API calls to fetch
  // experiences / preferences. Only available when TCF is enabled. Optional.
  fidesString: string | null;

  // Allows for explicit overrides on various internal API calls made from Fides.
  apiOptions: FidesApiOptions | null;

  // What the "GDPR Applies" field of TCF should default to
  fidesTcfGdprApplies: boolean;

  // Base URL for directory of fides.js scripts
  fidesJsBaseUrl: string;

  // A custom path to fetch OverrideOptions (e.g. "window.config.overrides"). Defaults to window.fides_overrides
  customOptionsPath: string | null;

  // Prevents the banner and modal from being dismissed
  preventDismissal: boolean;

  // Allows providing rich HTML descriptions
  allowHTMLDescription: boolean | null;

  // Encodes cookie as base64 on top of the default JSON string
  base64Cookie: boolean;
};

/**
 * Store the user's consent preferences on the cookie, as key -> boolean pairs, e.g.
 * {
 *   "data_sales": false,
 *   "analytics": true,
 *   ...
 * }
 */
export type CookieKeyConsent = {
  [cookieKey: string]: boolean | undefined;
};
/**
 * Store the user's identity values on the cookie, e.g.
 * {
 *   "fides_user_device_id": "1234-",
 *   "email": "jane@example.com",
 *   ...
 * }
 */
export type CookieIdentity = Record<string, string>;
/**
 * Store metadata about the cookie itself, e.g.
 * {
 *   "version": "0.9.0",
 *   "createdAt": "2023-01-01T12:00:00.000Z",
 *   ...
 * }
 */
export type CookieMeta = Record<string, string>;

export interface FidesCookie {
  consent: CookieKeyConsent;
  identity: CookieIdentity;
  fides_meta: CookieMeta;
  fides_string?: string;
  tcf_consent: TcfCookieConsent;
  tcf_version_hash?: ExperienceMeta["version_hash"];
}

export type GetPreferencesFnResp = {
  // Overrides the value for Fides.consent for the user’s notice-based preferences (e.g. { data_sales: false })
  consent?: CookieKeyConsent;
  // Overrides the value for Fides.fides_string for the user’s TCF+AC preferences (e.g. 1a2a3a.AAABA,1~123.121)
  fides_string?: string;
  // An explicit version hash for provided fides_string when calculating whether consent should be re-triggered
  version_hash?: string;
};

export type FidesApiOptions = {
  /**
   * Intake a custom function that is called instead of the internal Fides API to save user preferences.
   *
   * @param {object} consentMethod - method that was used to obtain consent
   * @param {object} consent - updated version of Fides.consent with the user's saved preferences for Fides notices
   * @param {string} fides_string - updated version of Fides.fides_string with the user's saved preferences for TC/AC/etc notices
   * @param {object} experience - current version of the privacy experience that was shown to the user
   */
  savePreferencesFn?: (
    consentMethod: ConsentMethod,
    consent: CookieKeyConsent,
    fides_string: string | undefined,
    experience: PrivacyExperience
  ) => Promise<void>;
  /**
   * Intake a custom function that is used to override users' saved preferences.
   *
   * @param {object} fides - global Fides obj containing global config options and other state at time of init
   */
  getPreferencesFn?: (fides: FidesConfig) => Promise<GetPreferencesFnResp>;
  /**
   * Intake a custom function that is used to fetch privacy experience.
   *
   * @param {string} userLocationString - user location
   * @param {string} fidesUserDeviceId - (deprecated) We no longer support handling user preferences on the experience using fidesUserDeviceId
   */
  getPrivacyExperienceFn?: (
    userLocationString: string,
    fidesUserDeviceId?: string | null
  ) => Promise<PrivacyExperience | EmptyExperience>;
  /**
   * Intake a custom function that is used to save notices served for reporting purposes.
   *
   * @param {object} request - consent served records to save
   */
  patchNoticesServedFn?: (
    request: RecordConsentServedRequest
  ) => Promise<RecordsServedResponse | null>;
};

export class SaveConsentPreference {
  consentPreference: UserConsentPreference;

  notice: PrivacyNotice;

  constructor(notice: PrivacyNotice, consentPreference: UserConsentPreference) {
    this.notice = notice;
    this.consentPreference = consentPreference;
  }
}

/**
 * Pre-parsed TC data and TC string for a CMP SDK:
 *
 * https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/IAB%20Tech%20Lab%20-%20CMP%20API%20v2.md#in-app-details
 */
export type TCMobileData = {
  /**
   * The unsigned integer ID of CMP SDK
   */
  IABTCF_CmpSdkID?: number;
  /**
   * The unsigned integer version number of CMP SDK
   */
  IABTCF_CmpSdkVersion?: number;
  /**
   * The unsigned integer representing the version of the TCF that these consents adhere to.
   */
  IABTCF_PolicyVersion?: number;
  /**
   * 1: GDPR applies in current context, 0 - GDPR does not apply in current context, None=undetermined
   */
  IABTCF_gdprApplies?: TCMobileDataVals.IABTCFgdprApplies;
  /**
   * Two-letter ISO 3166-1 alpha-2 code
   */
  IABTCF_PublisherCC?: string;
  /**
   * Vendors can use this value to determine whether consent for purpose one is required. 0: no special treatment. 1: purpose one not disclosed
   */
  IABTCF_PurposeOneTreatment?: TCMobileDataVals.IABTCFPurposeOneTreatment;
  /**
   * 1 - CMP uses customized stack descriptions and/or modified or supplemented standard illustrations.0 - CMP did not use a non-standard stack desc. and/or modified or supplemented Illustrations
   */
  IABTCF_UseNonStandardTexts?: TCMobileDataVals.IABTCFUseNonStandardTexts;
  /**
   * Fully encoded TC string
   */
  IABTCF_TCString?: string;
  /**
   * Binary string: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the consent status for Vendor ID n+1; false and true respectively. eg. '1' at index 0 is consent true for vendor ID 1
   */
  IABTCF_VendorConsents?: string;
  /**
   * Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the legitimate interest status for Vendor ID n+1; false and true respectively. eg. '1' at index 0 is legitimate interest established true for vendor ID 1
   */
  IABTCF_VendorLegitimateInterests?: string;
  /**
   * Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the consent status for purpose ID n+1; false and true respectively. eg. '1' at index 0 is consent true for purpose ID 1
   */
  IABTCF_PurposeConsents?: string;
  /**
   * Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the legitimate interest status for purpose ID n+1; false and true respectively. eg. '1' at index 0 is legitimate interest established true for purpose ID 1
   */
  IABTCF_PurposeLegitimateInterests?: string;
  /**
   * Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the opt-in status for special feature ID n+1; false and true respectively. eg. '1' at index 0 is opt-in true for special feature ID 1
   */
  IABTCF_SpecialFeaturesOptIns?: string;
  IABTCF_PublisherConsent?: string;
  IABTCF_PublisherLegitimateInterests?: string;
  IABTCF_PublisherCustomPurposesConsents?: string;
  IABTCF_PublisherCustomPurposesLegitimateInterests?: string;
};

export namespace TCMobileDataVals {
  /**
   * 1: GDPR applies in current context, 0 - GDPR does not apply in current context, None=undetermined
   */
  export enum IABTCFgdprApplies {
    "_0" = 0,
    "_1" = 1,
  }

  /**
   * Vendors can use this value to determine whether consent for purpose one is required. 0: no special treatment. 1: purpose one not disclosed
   */
  export enum IABTCFPurposeOneTreatment {
    "_0" = 0,
    "_1" = 1,
  }

  /**
   * 1 - CMP uses customized stack descriptions and/or modified or supplemented standard illustrations.0 - CMP did not use a non-standard stack desc. and/or modified or supplemented Illustrations
   */
  export enum IABTCFUseNonStandardTexts {
    "_0" = 0,
    "_1" = 1,
  }
}

/**
 * Supplements experience with developer-friendly meta information
 */
export type ExperienceMeta = {
  /**
   * A hashed value that can be compared to previously-fetched hash values to determine if the Experience has meaningfully changed
   */
  version_hash?: string;
  /**
   * The fides string (TC String + AC String) corresponding to a user opting in to all available options
   */
  accept_all_fides_string?: string;
  accept_all_fides_mobile_data?: TCMobileData;
  /**
   * The fides string (TC String + AC String) corresponding to a user opting out of all available options
   */
  reject_all_fides_string?: string;
  reject_all_fides_mobile_data?: TCMobileData;
};

export type PrivacyExperience = {
  region: string; // intentionally using plain string instead of Enum, since BE is susceptible to change
  component?: ComponentType; // deprecated- don't use
  disabled?: boolean;
  experience_config?: ExperienceConfig;
  id: string;
  created_at: string;
  updated_at: string;
  show_banner?: boolean; // deprecated- don't use
  privacy_notices?: Array<PrivacyNoticeWithPreference>;
  tcf_purpose_consents?: Array<TCFPurposeConsentRecord>;
  tcf_purpose_legitimate_interests?: Array<TCFPurposeLegitimateInterestsRecord>;
  tcf_special_purposes?: Array<TCFSpecialPurposeRecord>;
  tcf_features?: Array<TCFFeatureRecord>;
  tcf_special_features?: Array<TCFSpecialFeatureRecord>;
  tcf_vendor_consents?: Array<TCFVendorConsentRecord>;
  tcf_vendor_legitimate_interests?: Array<TCFVendorLegitimateInterestsRecord>;
  tcf_vendor_relationships?: Array<TCFVendorRelationships>;
  tcf_system_consents?: Array<TCFVendorConsentRecord>;
  tcf_system_legitimate_interests?: Array<TCFVendorLegitimateInterestsRecord>;
  tcf_system_relationships?: Array<TCFVendorRelationships>;
  gvl?: GVLJson;
  meta?: ExperienceMeta;
  gpp_settings?: GPPSettings;
};

export type ExperienceConfig = {
  translations: Array<ExperienceConfigTranslation>;
  banner_enabled?: BannerEnabled; // deprecated- don't use
  dismissable?: boolean;
  allow_language_selection?: boolean;
  custom_asset_id?: string;
  id: string;
  component: ComponentType;
  created_at: string;
  updated_at: string;
};

export type ExperienceConfigTranslation = {
  // will this have an id?
  language: string;
  accept_button_label?: string;
  acknowledge_button_label?: string;
  banner_description?: string;
  banner_enabled?: BannerEnabled; // deprecated - don't use
  banner_title?: string;
  description?: string;
  is_default?: boolean;
  privacy_policy_link_label?: string;
  privacy_policy_url?: string;
  privacy_preferences_link_label?: string;
  reject_button_label?: string;
  save_button_label?: string;
  title?: string;
  experience_config_history_id: string;
};

export type Cookies = {
  name: string;
  path?: string;
  domain?: string;
};

export enum PrivacyNoticeFramework {
  GPP_US_NATIONAL = "gpp_us_national",
  GPP_US_STATE = "gpp_us_state",
}

export type PrivacyNotice = {
  name?: string;
  notice_key: string;
  internal_description?: string;
  origin?: string;
  consent_mechanism?: ConsentMechanism;
  data_uses?: Array<string>;
  enforcement_level?: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  framework?: PrivacyNoticeFramework;
  gpp_field_mapping?: Array<GPPFieldMapping>;
  id: string;
  created_at: string;
  updated_at: string;
  cookies: Array<Cookies>;
  default_preference: UserConsentPreference;
  systems_applicable?: boolean;
  translations: Array<PrivacyNoticeTranslations>;
};

export type PrivacyNoticeTranslations = {
  id: string;
  language: string;
  title?: string;
  description?: string;
  version: number;
  privacy_notice_history_id: string;
};

// This type is exclusively used on front-end
export type PrivacyNoticeWithPreference = PrivacyNotice & {
  // Tracks preference to be shown via the UI / served via CMP
  current_preference?: UserConsentPreference;
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
  MODAL = "modal",
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

export type OverrideOptions = {
  fides_string: string;
  fides_disable_save_api: boolean;
  fides_disable_banner: boolean;
  fides_embed: boolean;
  fides_tcf_gdpr_applies: boolean;
};

export type FidesOptionsOverrides = Pick<
  FidesOptions,
  | "fidesString"
  | "fidesDisableSaveApi"
  | "fidesEmbed"
  | "fidesDisableBanner"
  | "fidesTcfGdprApplies"
>;

export type FidesOverrides = {
  optionsOverrides: Partial<FidesOptionsOverrides>;
  consentPrefsOverrides: GetPreferencesFnResp | null;
};

export enum ButtonType {
  PRIMARY = "primary",
  SECONDARY = "secondary",
  TERTIARY = "tertiary",
}

export enum ConsentMethod {
  BUTTON = "button", // deprecated- keeping for backwards-compatibility
  REJECT = "reject",
  ACCEPT = "accept",
  SAVE = "save",
  DISMISS = "dismiss",
  GPC = "gpc",
  INDIVIDUAL_NOTICE = "individual_notice",
}

export type PrivacyPreferencesRequest = {
  browser_identity: Identity;
  code?: string;
  fides_string?: string;
  preferences?: Array<ConsentOptionCreate>;
  purpose_consent_preferences?: Array<TCFPurposeSave>;
  purpose_legitimate_interests_preferences?: Array<TCFPurposeSave>;
  special_purpose_preferences?: Array<TCFSpecialPurposeSave>;
  vendor_consent_preferences?: Array<TCFVendorSave>;
  vendor_legitimate_interests_preferences?: Array<TCFVendorSave>;
  feature_preferences?: Array<TCFFeatureSave>;
  special_feature_preferences?: Array<TCFSpecialFeatureSave>;
  system_consent_preferences?: Array<TCFVendorSave>;
  system_legitimate_interests_preferences?: Array<TCFVendorSave>;
  policy_key?: string;
  privacy_experience_id?: string;
  user_geography?: string;
  method?: ConsentMethod;
  served_notice_history_id?: string;
};

export type ConsentOptionCreate = {
  privacy_notice_history_id: string;
  preference: UserConsentPreference;
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
  TCF_BANNER = "tcf_banner",
}
/**
 * Request body when indicating that notices were served in the UI
 */
export type RecordConsentServedRequest = {
  browser_identity: Identity;
  code?: string;
  privacy_notice_history_ids?: Array<string>;
  tcf_purpose_consents?: Array<number>;
  tcf_purpose_legitimate_interests?: Array<number>;
  tcf_special_purposes?: Array<number>;
  tcf_vendor_consents?: Array<string>;
  tcf_vendor_legitimate_interests?: Array<string>;
  tcf_features?: Array<number>;
  tcf_special_features?: Array<number>;
  tcf_system_consents?: Array<string>;
  tcf_system_legitimate_interests?: Array<string>;
  privacy_experience_id?: string;
  user_geography?: string;
  acknowledge_mode?: boolean;
  serving_component: ServingComponent;
};

/**
 * Response when saving that consent was served
 */
export type RecordsServedResponse = {
  served_notice_history_id: string;
  privacy_notice_history_ids: string[];
  tcf_purpose_consents: number[];
  tcf_purpose_legitimate_interests: number[];
  tcf_special_purposes: number[];
  tcf_vendor_consents: string[];
  tcf_vendor_legitimate_interests: string[];
  tcf_features: number[];
  tcf_special_features: number[];
  tcf_system_consents: string[];
  tcf_system_legitimate_interests: string[];
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
