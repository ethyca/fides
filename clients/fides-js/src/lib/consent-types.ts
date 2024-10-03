import type { Fides, FidesEventType, FidesOptions } from "../docs";
import type { gtm } from "../integrations/gtm";
import type { meta } from "../integrations/meta";
import type { shopify } from "../integrations/shopify";
import type { FidesEventDetail } from "./events";
import type { GPPFieldMapping, GPPSettings } from "./gpp/types";
import type {
  GVLJson,
  TCFFeatureRecord,
  TCFFeatureSave,
  TcfOtherConsent,
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

export type EmptyExperience = Record<PropertyKey, never>;

export interface FidesConfig {
  // Set the consent defaults from a "legacy" Privacy Center config.json.
  consent?: LegacyConsentConfig;
  // Set the "experience" to be used for this Fides.js instance -- overrides the "legacy" config.
  // If defined or is empty, Fides.js will not fetch experience config.
  // If undefined, Fides.js will attempt to fetch its own experience config.
  experience?: PrivacyExperience | PrivacyExperienceMinimal | EmptyExperience;
  // Set the geolocation for this Fides.js instance. If *not* set, Fides.js will fetch its own geolocation.
  geolocation?: UserGeolocation;
  // Set the property id for this Fides.js instance. If *not* set, property id will not be saved in the consent preferences or notices served.
  propertyId?: string;
  // Global options for this Fides.js instance
  options: FidesInitOptions;
}

/**
 * Defines all the options supported by `Fides.init()`. Many of these are
 * effectively constants that aren't meant to be set at runtime by customers,
 * but we do allow _some_ of them to be overriden via query params / cookie
 * values / window object. See the {@link FidesOptions} docs for details.
 */
export interface FidesInitOptions {
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

  // ID of the DOM element that should trigger the consent modal (default: "fides-modal-link")
  // If set to empty string "", fides.js will not attempt to bind the modal link to the click handler
  modalLinkId: string | null;

  // URL for the Privacy Center, used to customize consent preferences. Required.
  privacyCenterUrl: string;

  // URL for the Fides API, used to fetch and save consent preferences. Required.
  fidesApiUrl: string;

  // Whether we should show the TCF modal
  tcfEnabled: boolean;

  // Whether to include the GPP extension
  gppEnabled: boolean;

  // Whether we should "embed" the fides.js overlay UI (ie. “Layer 2”) into a web page instead of as a pop-up
  // overlay, and never render the banner (ie. “Layer 1”).
  fidesEmbed: boolean;

  // Whether we should disable saving consent preferences to the Fides API.
  fidesDisableSaveApi: boolean;

  // Whether we should only disable saving notices served to the Fides API.
  fidesDisableNoticesServedApi: boolean;

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

  // A custom path to fetch FidesOptions (e.g. "window.config.overrides"). Defaults to window.fides_overrides
  customOptionsPath: string | null;

  // Prevents the banner and modal from being dismissed
  preventDismissal: boolean;

  // Allows providing rich HTML descriptions
  allowHTMLDescription: boolean | null;

  // Encodes cookie as base64 on top of the default JSON string
  base64Cookie: boolean;

  // Allows specifying the preferred locale used for translations
  fidesLocale?: string;

  // Defines default primary color for consent components, but can still be overridden with overrides or custom CSS
  fidesPrimaryColor: string | null;

  // Shows fides.js overlay UI on load deleting the fides_consent cookie as if no preferences have been saved
  fidesClearCookie: boolean;

  // Whether cookies on subdomains should be deleted when user opts out
  automaticSubdomainCookieDeletion: boolean;
}

/**
 * Defines the exact interface used for the `Fides` global object. Note that we
 * extend the documented `Fides` interface here to provide some narrower, more
 * specific types. This is mostly for legacy purposes, but also since we want to
 * ensure that the documented interface isn't overly specific in areas we may
 * need to change.
 */
export interface FidesGlobal extends Fides {
  cookie?: FidesCookie;
  config?: FidesConfig;
  consent: NoticeConsent;
  experience?: PrivacyExperience | PrivacyExperienceMinimal | EmptyExperience;
  fides_meta: FidesJSMeta;
  fides_string?: string | undefined;
  geolocation?: UserGeolocation;
  identity: FidesJSIdentity;
  initialized: boolean;
  options: FidesInitOptions;
  saved_consent: NoticeConsent;
  tcf_consent: TcfOtherConsent;
  gtm: typeof gtm;
  init: (config?: FidesConfig) => Promise<void>;
  meta: typeof meta;
  onFidesEvent: (
    type: FidesEventType,
    callback: (evt: FidesEventDetail) => void,
  ) => () => void;
  reinitialize: () => Promise<void>;
  shopify: typeof shopify;
  shouldShowExperience: () => boolean;
  showModal: () => void;
}

/**
 * Store the user's consent preferences as notice_key -> boolean pairs, e.g.
 * {
 *   "data_sales": false,
 *   "analytics": true,
 *   ...
 * }
 */
export type NoticeConsent = Record<string, boolean>;

/**
 * Store the user's identity values, e.g.
 * {
 *   "fides_user_device_id": "1234-",
 *   "email": "jane@example.com",
 *   ...
 * }
 */
export type FidesJSIdentity = Record<string, string>;

/**
 * Store metadata about the cookie itself, e.g.
 * {
 *   "version": "0.9.0",
 *   "createdAt": "2023-01-01T12:00:00.000Z",
 *   "consentMethod": "accept",
 *   ...
 * }
 */
export type FidesJSMeta = Record<string, string>;

export interface FidesCookie {
  consent: NoticeConsent;
  identity: FidesJSIdentity;
  fides_meta: FidesJSMeta;
  fides_string?: string;
  tcf_consent: TcfOtherConsent;
  tcf_version_hash?: ExperienceMeta["version_hash"];
}

export type GetPreferencesFnResp = {
  // Overrides the value for Fides.consent for the user’s notice-based preferences (e.g. { data_sales: false })
  consent?: NoticeConsent;
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
    consent: NoticeConsent,
    fides_string: string | undefined,
    experience: PrivacyExperience | PrivacyExperienceMinimal,
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
  getPrivacyExperienceFn?: <T>(
    userLocationString: string,
    fidesUserDeviceId?: string | null,
  ) => Promise<T | EmptyExperience>;
  /**
   * Intake a custom function that is used to save notices served for reporting purposes.
   *
   * @param {object} request - consent served records to save
   */
  patchNoticesServedFn?: (
    request: RecordConsentServedRequest,
  ) => Promise<RecordsServedResponse | null>;
};

export class SaveConsentPreference {
  consentPreference: UserConsentPreference;

  notice: PrivacyNotice;

  noticeHistoryId?: string;

  constructor(
    notice: PrivacyNotice,
    consentPreference: UserConsentPreference,
    noticeHistoryId?: string,
  ) {
    this.notice = notice;
    this.consentPreference = consentPreference;
    this.noticeHistoryId = noticeHistoryId;
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

/**
 * Expected API response for a PrivacyExperience
 *
 * NOTE: This type is slightly-edited version of the autogenerated
 * "PrivacyExperienceResponse" type, to either tighten or relax the types in
 * FidesJS as needed by the client-code, so these types should be updated with care!
 */
export type PrivacyExperience = {
  id: string;
  created_at: string;
  updated_at: string;
  region: string; // NOTE: uses a generic string instead of a region enum, as this changes often
  component?: ComponentType;
  gpp_settings?: GPPSettings; // NOTE: uses our client-side GPPSettings type
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

  /**
   * @deprecated For backwards compatibility purposes, whether the Experience should show a banner.
   */
  show_banner?: boolean;
  /**
   * The Privacy Notices associated with this experience, if applicable
   */
  privacy_notices?: Array<PrivacyNoticeWithPreference>; // NOTE: uses our client-side PrivacyNoticeWithPreference type
  /**
   * The Experience Config and its translations
   */
  experience_config?: ExperienceConfig; // NOTE: uses our client-side ExperienceConfig type
  gvl?: GVLJson; // NOTE: uses our client-side GVLJson type
  meta?: ExperienceMeta;
  available_locales?: string[];
  vendor_count?: number;
  minimal_tcf?: boolean;
};

interface ExperienceConfigTranslationMinimal
  extends Partial<ExperienceConfigTranslation> {
  language: string;
  privacy_experience_config_history_id: string;
}

export interface ExperienceConfigMinimal
  extends Pick<
    ExperienceConfig,
    "component" | "auto_detect_language" | "dismissable"
  > {
  translations: ExperienceConfigTranslationMinimal[];
}

export interface PrivacyExperienceMinimal
  extends Pick<
    PrivacyExperience,
    | "id"
    | "available_locales"
    | "gpp_settings"
    | "vendor_count"
    | "minimal_tcf"
    | "gvl"
  > {
  experience_config: ExperienceConfigMinimal;
  vendor_count?: number;
  meta?: Pick<ExperienceMeta, "version_hash">;
  tcf_purpose_names?: string[];
  tcf_special_feature_names?: string[];
  tcf_purpose_consent_ids?: number[];
  tcf_purpose_legitimate_interest_ids?: number[];
  tcf_special_purpose_ids?: number[];
  tcf_feature_ids?: number[];
  tcf_special_feature_ids?: number[];
  tcf_vendor_consent_ids?: string[];
  tcf_vendor_legitimate_interest_ids?: string[];
  tcf_system_consent_ids?: string[];
  tcf_system_legitimate_interest_ids?: string[];
}

/**
 * Expected API response for an ExperienceConfig
 *
 * NOTE: This type is slightly-edited version of the autogenerated
 * "ExperienceConfigResponseNoNotices" type, to either tighten or relax the
 * types in FidesJS as needed by the client-code, so these types should be
 * updated with care!
 */
export type ExperienceConfig = {
  name?: string;
  disabled?: boolean;
  dismissable?: boolean;
  show_layer1_notices?: boolean;
  layer1_button_options?: Layer1ButtonOption;
  allow_language_selection?: boolean;
  auto_detect_language?: boolean;
  modal_link_label?: string;

  /**
   * List of regions that apply to this ExperienceConfig.
   *
   * NOTE: we modify this type on the client to be an array of strings instead
   * of region enums, as those will change often. We also mark it as an optional
   * array, even though the API provides it, since we want to avoid relying on
   * these regions on the client.
   */
  regions?: Array<string>;
  id: string;
  created_at: string;
  updated_at: string;
  component: ComponentType;

  /**
   * List of all available translations for this ExperienceConfig
   *
   * NOTE: edited to be a *required* field on the client-side types for
   * simplicity, since the API actually guarantees this will always be present.
   * This also uses our client-side ExperienceConfigTranslation type.
   */
  translations: Array<ExperienceConfigTranslation>;

  /**
   * @deprecated see fields on translations instead
   */
  language?: string; // NOTE: uses a generic string instead of a language enum, as this changes often
  /**
   * @deprecated see fields on translations instead
   */
  accept_button_label?: string;
  /**
   * @deprecated see fields on translations instead
   */
  acknowledge_button_label?: string;
  /**
   * @deprecated see fields on translations instead
   */
  banner_title?: string;
  /**
   * @deprecated see fields on translations instead
   */
  is_default?: boolean;
  /**
   * @deprecated see fields on translations instead
   */
  privacy_policy_link_label?: string;
  /**
   * @deprecated see fields on translations instead
   */
  privacy_policy_url?: string;
  /**
   * @deprecated see fields on translations instead
   */
  privacy_preferences_link_label?: string;
  /**
   * @deprecated see fields on translations instead
   */
  reject_button_label?: string;
  /**
   * @deprecated see fields on translations instead
   */
  save_button_label?: string;
  /**
   * @deprecated see fields on translations instead
   */
  title?: string;
  /**
   * @deprecated see fields on translations instead
   */
  banner_description?: string;
  /**
   * @deprecated see fields on translations instead
   */
  description?: string;
};

/**
 * Expected API response for an ExperienceConfigTranslation
 *
 * NOTE: This type is slightly-edited version of the autogenerated
 * "ExperienceTranslationResponse" type, to either tighten or relax the
 * types in FidesJS as needed by the client-code, so these types should be
 * updated with care!
 */
export type ExperienceConfigTranslation = {
  language: string; // NOTE: uses a generic string instead of a language enum, as this changes often
  accept_button_label?: string;
  acknowledge_button_label?: string;
  banner_title?: string;
  is_default?: boolean;
  privacy_policy_link_label?: string;
  privacy_policy_url?: string;
  privacy_preferences_link_label?: string;
  reject_button_label?: string;
  save_button_label?: string;
  title?: string;
  banner_description?: string;
  description?: string;
  purpose_header?: string;
  privacy_experience_config_history_id: string;
  modal_link_label?: string;
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

/**
 * Expected API response for a PrivacyNotice
 *
 * NOTE: This type is slightly-edited version of the autogenerated
 * "PrivacyNoticeResponse" type to either tighten or relax the types in FidesJS
 * as needed by the client-code, but we try to be as close as possible to the
 * API types!
 */
export type PrivacyNotice = {
  name?: string;
  notice_key: string; // NOTE: edited to be *required* on the client for simplicity (since the API actually guarantees this!)
  internal_description?: string;
  consent_mechanism?: ConsentMechanism;
  data_uses?: Array<string>;
  enforcement_level?: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  framework?: PrivacyNoticeFramework;
  default_preference?: UserConsentPreference;
  id: string;
  origin?: string;
  created_at: string;
  updated_at: string;
  cookies: Array<Cookies>;
  systems_applicable?: boolean;

  /**
   * List of all available translations for this PrivacyNotice
   *
   * NOTE: edited to be a *required* field on the client-side types for
   * simplicity, since the API actually guarantees this will always be present.
   * This also uses our client-side PrivacyNoticeTranslation type.
   */
  translations: Array<PrivacyNoticeTranslation>;
  gpp_field_mapping?: Array<GPPFieldMapping>;
};

/**
 * Expected API response for a PrivacyNoticeTranslation
 *
 * NOTE: This type is slightly-edited version of the autogenerated
 * "NoticeTranslationResponse" type to either tighten or relax the types in
 * FidesJS as needed by the client-code, but we try to be as close as possible
 * to the API types!
 */
export type PrivacyNoticeTranslation = {
  language: string; // NOTE: uses a generic string instead of a language enum, as this changes often
  title?: string;
  description?: string;
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
  TCF = "tcf",
}

// NOTE: This (and most enums!) could reasonably be replaced by string union
// types in Typescript and would be a bit easier to handle...
export enum ComponentType {
  OVERLAY = "overlay", // deprecated, replaced by BANNER_AND_MODAL
  BANNER_AND_MODAL = "banner_and_modal",
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

/**
 * Re-export the FidesOptions interface from src/docs; mostly for convenience as
 * a lot of code wants to import from this consent-types.ts file!
 */
export { FidesOptions };

export type OverrideExperienceTranslations = {
  fides_title: string;
  fides_description: string;
  fides_privacy_policy_url: string;
  fides_override_language: string;
};

/**
 * Select the subset of FidesInitOptions that can be overriden at runtime using
 * one of the customer-provided FidesOptions properties above. There's a 1:1
 * correspondence here, but note that we use snake_case for the runtime options
 * and then convert to camelCase variables for the `Fides.init({ options })`
 * invocation itself.
 */
export type FidesInitOptionsOverrides = Pick<
  FidesInitOptions,
  | "fidesString"
  | "fidesDisableSaveApi"
  | "fidesDisableNoticesServedApi"
  | "fidesEmbed"
  | "fidesDisableBanner"
  | "fidesTcfGdprApplies"
  | "fidesLocale"
  | "fidesPrimaryColor"
  | "fidesClearCookie"
>;

export type FidesExperienceTranslationOverrides = {
  title: string;
  description: string;
  privacy_policy_url: string;
  override_language: string;
};

export type FidesOverrides = {
  optionsOverrides: Partial<FidesInitOptionsOverrides>;
  consentPrefsOverrides: GetPreferencesFnResp | null;
  experienceTranslationOverrides: Partial<FidesExperienceTranslationOverrides>;
};

export enum OverrideType {
  OPTIONS = "options",
  EXPERIENCE_TRANSLATION = "language",
}

export enum ButtonType {
  PRIMARY = "primary",
  SECONDARY = "secondary",
  TERTIARY = "tertiary",
}

export enum Layer1ButtonOption {
  // defines the buttons to show in the layer 1 banner
  ACKNOWLEDGE = "acknowledge", // show acknowledge button
  OPT_IN_OPT_OUT = "opt_in_opt_out", // show opt in and opt out buttons
}

export enum ConsentMethod {
  BUTTON = "button", // deprecated- keeping for backwards-compatibility
  REJECT = "reject",
  ACCEPT = "accept",
  SAVE = "save",
  DISMISS = "dismiss",
  GPC = "gpc",
  INDIVIDUAL_NOTICE = "individual_notice",
  ACKNOWLEDGE = "acknowledge",
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
  property_id?: string;

  /**
   * @deprecated has no effect; use privacy_experience_config_history_id instead!
   */
  privacy_experience_id?: string;
  privacy_experience_config_history_id?: string;
  user_geography?: string;
  method?: ConsentMethod;
  served_notice_history_id?: string;
  source?: string;
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
  OVERLAY = "overlay", // deprecated, use "modal" instead
  MODAL = "modal",
  BANNER = "banner",
  PRIVACY_CENTER = "privacy_center",
  TCF_OVERLAY = "tcf_overlay",
  TCF_BANNER = "tcf_banner",
}
/**
 * Request body when indicating that notices were served in the UI
 */
export type RecordConsentServedRequest = {
  served_notice_history_id: string; // a generated uuidv4 string

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
  /**
   * @deprecated has no effect; use privacy_experience_config_history_id instead!
   */
  privacy_experience_id?: string;
  privacy_experience_config_history_id?: string;
  user_geography?: string;
  acknowledge_mode?: boolean;
  serving_component: string; // NOTE: uses a generic string instead of an enum
  property_id?: string;
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
