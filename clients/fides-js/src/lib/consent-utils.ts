import { isConsentOverride } from "./common-utils";
import {
  FIDES_OVERRIDE_EXPERIENCE_LANGUAGE_VALIDATOR_MAP,
  FIDES_OVERRIDE_OPTIONS_VALIDATOR_MAP,
  VALID_ISO_3166_LOCATION_REGEX,
} from "./consent-constants";
import { ConsentContext } from "./consent-context";
import {
  ComponentType,
  ConsentMechanism,
  ConsentMethod,
  EmptyExperience,
  FidesCookie,
  FidesExperienceLanguageValidatorMap,
  FidesInitOptions,
  FidesOverrideValidatorMap,
  FidesWindowOverrides,
  GpcStatus,
  NoticeConsent,
  OverrideType,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  PrivacyNotice,
  PrivacyNoticeItem,
  PrivacyNoticeWithPreference,
  SaveConsentPreference,
  UserConsentPreference,
  UserGeolocation,
} from "./consent-types";
import {
  noticeHasConsentInCookie,
  transformConsentToFidesUserPreference,
} from "./shared-consent-utils";
import { TcfModelsRecord } from "./tcf/types";

/**
 * Returns true if the provided input is a valid PrivacyExperience object.
 *
 * This includes the special case where the input is an empty object ({}), which
 * is a valid response when the API does not find a PrivacyExperience configured
 * for the given geolocation.
 */
export const isPrivacyExperience = (
  obj:
    | PrivacyExperience
    | PrivacyExperienceMinimal
    | undefined
    | EmptyExperience,
): obj is PrivacyExperience => {
  // Return false for all non-object types
  if (!obj || typeof obj !== "object") {
    return false;
  }

  // Treat an empty object ({}) as a valid experience
  if (Object.keys(obj).length === 0) {
    return true;
  }

  // Require at least an "id" field to be considered an experience
  if ("id" in obj) {
    return true;
  }
  return false;
};

export const allNoticesAreDefaultOptIn = (
  notices: Array<PrivacyNoticeWithPreference> | undefined,
): boolean =>
  Boolean(
    notices &&
      notices.every(
        (notice) => notice.default_preference === UserConsentPreference.OPT_IN,
      ),
  );

/**
 * Construct user location str to be ingested by Fides API
 * Returns null if geolocation cannot be constructed by provided params, e.g. us_ca
 */
export const constructFidesRegionString = (
  geoLocation?: UserGeolocation | null,
): string | null => {
  fidesDebugger("constructing geolocation...");
  if (!geoLocation) {
    fidesDebugger(
      "cannot construct user location since geoLocation is undefined or null",
    );
    return null;
  }
  if (
    geoLocation.location &&
    VALID_ISO_3166_LOCATION_REGEX.test(geoLocation.location)
  ) {
    // Fides backend requires underscore deliminator
    const regionString = geoLocation.location.replace("-", "_").toLowerCase();
    fidesDebugger(`using geolocation: ${regionString}`);
    return regionString;
  }
  if (geoLocation.country && geoLocation.region) {
    const regionString = `${geoLocation.country.toLowerCase()}_${geoLocation.region.toLowerCase()}`;
    fidesDebugger(`using geolocation: ${regionString}`);
    return regionString;
  }
  fidesDebugger(
    "cannot construct user location from provided geoLocation params...",
  );
  return null;
};

/**
 * Validate the fides global config options. If invalid, we cannot make API calls to Fides or link to the Privacy Center.
 */
export const validateOptions = (options: FidesInitOptions): boolean => {
  // Check if options is an invalid type
  fidesDebugger("Validating Fides config options...", options);
  if (typeof options !== "object") {
    return false;
  }

  if (!options.fidesApiUrl) {
    fidesDebugger("Invalid options: fidesApiUrl is required!");
    return false;
  }

  if (!options.privacyCenterUrl) {
    fidesDebugger("Invalid options: privacyCenterUrl is required!");
    return false;
  }

  try {
    // eslint-disable-next-line no-new
    new URL(options.privacyCenterUrl);
    // eslint-disable-next-line no-new
    new URL(options.fidesApiUrl);
  } catch (e) {
    fidesDebugger(
      "Invalid options: privacyCenterUrl or fidesApiUrl is an invalid URL!",
      options.privacyCenterUrl,
    );
    return false;
  }

  return true;
};

export const getOverrideValidatorMapByType = (
  overrideType: OverrideType,
):
  | FidesOverrideValidatorMap[]
  | FidesExperienceLanguageValidatorMap[]
  | null => {
  // eslint-disable-next-line default-case
  switch (overrideType) {
    case OverrideType.OPTIONS:
      return FIDES_OVERRIDE_OPTIONS_VALIDATOR_MAP;
    case OverrideType.EXPERIENCE_TRANSLATION:
      return FIDES_OVERRIDE_EXPERIENCE_LANGUAGE_VALIDATOR_MAP;
    default:
      return null;
  }
};

/**
 * Determines whether experience is valid and relevant notices exist within the experience
 */
export const experienceIsValid = (
  effectiveExperience:
    | PrivacyExperience
    | PrivacyExperienceMinimal
    | undefined
    | EmptyExperience,
): boolean => {
  if (!isPrivacyExperience(effectiveExperience)) {
    fidesDebugger("No relevant experience found.");
    return false;
  }
  const expConfig = effectiveExperience.experience_config;
  if (!expConfig) {
    fidesDebugger("No config found for experience.");
    return false;
  }
  if (
    !(
      expConfig.component === ComponentType.MODAL ||
      expConfig.component === ComponentType.BANNER_AND_MODAL ||
      expConfig.component === ComponentType.TCF_OVERLAY ||
      expConfig.component === ComponentType.HEADLESS
    )
  ) {
    fidesDebugger(
      "No experience found with modal, banner_and_modal, tcf_overlay, or headless component.",
    );
    return false;
  }
  if (
    expConfig.component === ComponentType.BANNER_AND_MODAL &&
    !(
      effectiveExperience.privacy_notices &&
      effectiveExperience.privacy_notices.length > 0
    )
  ) {
    fidesDebugger(`Privacy experience has no notices.`);
    return false;
  }

  return true;
};

/**
 * Returns default TCF preference
 */
export const getTcfDefaultPreference = (tcfObject: TcfModelsRecord) =>
  tcfObject.default_preference ?? UserConsentPreference.OPT_OUT;

/**
 * Returns true if there are notices in the experience that require a user preference
 * or if an experience's version hash does not match up.
 */
export const shouldResurfaceBanner = (
  experience:
    | PrivacyExperience
    | PrivacyExperienceMinimal
    | EmptyExperience
    | undefined,
  cookie: FidesCookie | undefined,
  savedConsent: NoticeConsent,
  options?: FidesInitOptions,
): boolean => {
  // Never resurface banner if it is disabled
  if (options?.fidesDisableBanner) {
    return false;
  }
  // Never surface banner if there's no experience
  if (!isPrivacyExperience(experience)) {
    return false;
  }
  // Always resurface banner for TCF unless the saved version_hash matches
  if (
    experience.experience_config?.component === ComponentType.TCF_OVERLAY &&
    !!cookie
  ) {
    if (experience.meta?.version_hash) {
      return experience.meta.version_hash !== cookie.tcf_version_hash;
    }
    return true;
  }
  // Never surface banner for modal-only or headless experiences
  if (
    experience.experience_config?.component === ComponentType.MODAL ||
    experience.experience_config?.component === ComponentType.HEADLESS
  ) {
    return false;
  }
  // Do not surface banner for null or empty notices
  if (!(experience as PrivacyExperience)?.privacy_notices?.length) {
    return false;
  }
  // Always resurface if there is no prior consent
  if (!savedConsent) {
    return true;
  }
  // Never surface banner if consent was set by override
  if (options && isConsentOverride(options)) {
    return false;
  }

  // resurface in the special case where the saved consent
  // is only recorded with a consentMethod of "dismiss" or "gpc"
  if (
    cookie &&
    (cookie.fides_meta.consentMethod === ConsentMethod.GPC ||
      cookie.fides_meta.consentMethod === ConsentMethod.DISMISS)
  ) {
    return true;
  }

  // Lastly, if we do have a prior consent state, resurface if we find *any*
  // notices that don't have prior consent in that state
  const hasConsentInCookie = (
    experience as PrivacyExperience
  ).privacy_notices?.every((notice) =>
    noticeHasConsentInCookie(notice, savedConsent),
  );
  return !hasConsentInCookie;
};

/**
 * Descend down the provided path on the "window" object and return the nested
 * override options object located at the given path.
 *
 * If any part of the path is invalid, return `undefined`.
 *
 *
 * For example, given a window object like this:
 * ```
 * window.custom_overrides = { nested_obj: { fides_string: "foo" } } };
 * ```
 *
 * Then expect the following:
 * ```
 * const overrides = getWindowObjFromPath(["window", "custom_overrides", "nested_obj"])
 * console.assert(overrides.fides_string === "foo");
 * ```
 */
export const getWindowObjFromPath = (
  path: string[],
): FidesWindowOverrides | undefined => {
  // Implicitly start from the global "window" object
  if (path[0] === "window") {
    path.shift();
  }
  // Descend down the provided path (starting from `window`)
  let record: any = window;
  while (path.length > 0) {
    const key = path.shift();
    // If we ever encounter an invalid key or a non-object value, return undefined
    if (typeof key === "undefined" || typeof record[key] !== "object") {
      return undefined;
    }
    // Keep descending!
    record = record[key];
  }
  return record;
};

export const getGpcStatusFromNotice = ({
  value,
  notice,
  consentContext,
}: {
  value: boolean;
  notice: PrivacyNotice;
  consentContext: ConsentContext;
}) => {
  // If GPC is not enabled, it won't be applied at all.
  if (
    !consentContext.globalPrivacyControl ||
    !notice.has_gpc_flag ||
    notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY
  ) {
    return GpcStatus.NONE;
  }

  // if gpc is enabled for the notice and consent is opt-out (false)
  if (!value) {
    return GpcStatus.APPLIED;
  }

  return GpcStatus.OVERRIDDEN;
};

export const defaultShowModal = () => {
  fidesDebugger("The current experience does not support displaying a modal.");
};

/**
 * Parses a comma-separated string of notice keys into an array of strings.
 * Handles undefined input, trims whitespace, and filters out empty strings.
 */
export const parseFidesDisabledNotices = (
  value: string | undefined,
): string[] => {
  if (!value) {
    return [];
  }

  return value
    .split(",")
    .map((key) => key.trim())
    .filter(Boolean);
};

export const createConsentPreferencesToSave = (
  privacyNoticeList: PrivacyNoticeItem[],
  enabledPrivacyNoticeKeys: string[],
): SaveConsentPreference[] =>
  privacyNoticeList.map((item) => {
    const userPreference = transformConsentToFidesUserPreference(
      enabledPrivacyNoticeKeys.includes(item.notice.notice_key),
      item.notice.consent_mechanism,
    );
    return new SaveConsentPreference(
      item.notice,
      userPreference,
      item.bestTranslation?.privacy_notice_history_id,
    );
  });

/**
 * Encodes consent data into a base64 string for the Notice Consent slot
 * @param consentData Object mapping notice keys to boolean consent values
 * @returns Base64 encoded string representation of the consent data
 */
export const encodeNoticeConsentString = (consentData: {
  [noticeKey: string]: boolean | 0 | 1;
}): string => {
  try {
    const jsonString = JSON.stringify(consentData);
    return btoa(jsonString.replace(/\s/g, ""));
  } catch (error) {
    throw new Error("Failed to encode Notice Consent string:", {
      cause: error,
    });
  }
};

/**
 * Decodes a base64 Notice Consent string back into consent data
 * @param base64String The base64 encoded Notice Consent string
 * @returns Decoded consent data object or null if decoding fails
 */
export const decodeNoticeConsentString = (
  base64String: string,
): {
  [noticeKey: string]: boolean;
} => {
  if (!base64String) {
    return {};
  }

  try {
    const jsonString = atob(base64String);
    const parsedData = JSON.parse(jsonString);

    // Convert any numeric values (1 or 0) to boolean
    return Object.fromEntries(
      Object.entries(parsedData).map(([key, value]) => [
        key,
        value === 0 || value === 1 ? !!value : Boolean(value),
      ]),
    );
  } catch (error) {
    throw new Error("Failed to decode Notice Consent string:", {
      cause: error,
    });
  }
};
