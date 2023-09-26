import { ConsentContext } from "./consent-context";
import {
  ComponentType,
  ConsentMechanism,
  EmptyExperience,
  FidesOptions,
  GpcStatus,
  PrivacyExperience,
  PrivacyNotice,
  UserConsentPreference,
  UserGeolocation,
  VALID_ISO_3166_LOCATION_REGEX,
} from "./consent-types";
import { TCFPurposeRecord } from "./tcf/types";

/**
 * Wrapper around 'console.log' that only logs output when the 'debug' banner
 * option is truthy
 */
type ConsoleLogParameters = Parameters<typeof console.log>;
export const debugLog = (
  enabled: boolean,
  ...args: ConsoleLogParameters
): void => {
  if (enabled) {
    // eslint-disable-next-line no-console
    console.log(...args);
  }
};

/**
 * Returns true if the provided input is a valid PrivacyExperience object.
 *
 * This includes the special case where the input is an empty object ({}), which
 * is a valid response when the API does not find a PrivacyExperience configured
 * for the given geolocation.
 */
export const isPrivacyExperience = (
  obj: PrivacyExperience | undefined | EmptyExperience
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

/**
 * Construct user location str to be ingested by Fides API
 * Returns null if geolocation cannot be constructed by provided params, e.g. us_ca
 */
export const constructFidesRegionString = (
  geoLocation?: UserGeolocation | null,
  debug: boolean = false
): string | null => {
  debugLog(debug, "constructing geolocation...");
  if (!geoLocation) {
    debugLog(
      debug,
      "cannot construct user location since geoLocation is undefined or null"
    );
    return null;
  }
  if (
    geoLocation.location &&
    VALID_ISO_3166_LOCATION_REGEX.test(geoLocation.location)
  ) {
    // Fides backend requires underscore deliminator
    return geoLocation.location.replace("-", "_").toLowerCase();
  }
  if (geoLocation.country && geoLocation.region) {
    return `${geoLocation.country.toLowerCase()}_${geoLocation.region.toLowerCase()}`;
  }
  // DEFER: return geoLocation.country when BE supports filtering by just country
  // see https://github.com/ethyca/fides/issues/3300
  debugLog(
    debug,
    "cannot construct user location from provided geoLocation params..."
  );
  return null;
};

/**
 * Convert a user consent preference into true/false
 */
export const transformUserPreferenceToBoolean = (
  preference: UserConsentPreference | undefined
) => {
  if (!preference) {
    return false;
  }
  if (preference === UserConsentPreference.OPT_OUT) {
    return false;
  }
  if (preference === UserConsentPreference.OPT_IN) {
    return true;
  }
  return preference === UserConsentPreference.ACKNOWLEDGE;
};

/**
 * Convert a true/false consent to Fides user consent preference
 */
export const transformConsentToFidesUserPreference = (
  consented: boolean,
  consentMechanism?: ConsentMechanism
): UserConsentPreference => {
  if (consented) {
    if (consentMechanism === ConsentMechanism.NOTICE_ONLY) {
      return UserConsentPreference.ACKNOWLEDGE;
    }
    return UserConsentPreference.OPT_IN;
  }
  return UserConsentPreference.OPT_OUT;
};

/**
 * Validate the fides global config options. If invalid, we cannot make API calls to Fides or link to the Privacy Center.
 */
export const validateOptions = (options: FidesOptions): boolean => {
  // Check if options is an invalid type
  debugLog(
    options.debug,
    "Validating Fides consent overlay options...",
    options
  );
  if (typeof options !== "object") {
    return false;
  }

  if (!options.fidesApiUrl) {
    debugLog(options.debug, "Invalid options: fidesApiUrl is required!");
    return false;
  }

  if (!options.privacyCenterUrl) {
    debugLog(options.debug, "Invalid options: privacyCenterUrl is required!");
    return false;
  }

  try {
    // eslint-disable-next-line no-new
    new URL(options.privacyCenterUrl);
    // eslint-disable-next-line no-new
    new URL(options.fidesApiUrl);
  } catch (e) {
    debugLog(
      options.debug,
      "Invalid options: privacyCenterUrl or fidesApiUrl is an invalid URL!",
      options.privacyCenterUrl
    );
    return false;
  }

  return true;
};

/**
 * Determines whether experience is valid and relevant notices exist within the experience
 */
export const experienceIsValid = (
  effectiveExperience: PrivacyExperience | undefined | EmptyExperience,
  options: FidesOptions
): boolean => {
  if (!isPrivacyExperience(effectiveExperience)) {
    debugLog(
      options.debug,
      "No relevant experience found. Skipping overlay initialization."
    );
    return false;
  }
  if (
    effectiveExperience.component !== ComponentType.OVERLAY &&
    effectiveExperience.component !== ComponentType.TCF_OVERLAY
  ) {
    debugLog(
      options.debug,
      "No experience found with overlay component. Skipping overlay initialization."
    );
    return false;
  }
  if (
    effectiveExperience.component === ComponentType.OVERLAY &&
    !(
      effectiveExperience.privacy_notices &&
      effectiveExperience.privacy_notices.length > 0
    )
  ) {
    debugLog(
      options.debug,
      `Privacy experience has no notices. Skipping overlay initialization.`
    );
    return false;
  }
  // TODO: add condition for not rendering TCF
  if (!effectiveExperience.experience_config) {
    debugLog(
      options.debug,
      "No experience config found with for experience. Skipping overlay initialization."
    );
    return false;
  }

  return true;
};

/** Returns true if a list of records has any current preference at all */
const hasCurrentPreference = (
  records: Pick<TCFPurposeRecord, "current_preference">[] | undefined
) => {
  if (!records || records.length === 0) {
    return false;
  }
  return records.some((record) => record.current_preference);
};

const hasActionNeededTcfPreference = (
  records: Pick<TCFPurposeRecord, "current_preference">[] | undefined
) => {
  if (!records || records.length === 0) {
    return false;
  }
  return records.some((record) => record.current_preference == null);
};

/**
 * Returns true if the user has any saved TCF preferences
 */
export const hasSavedTcfPreferences = (experience: PrivacyExperience) =>
  hasCurrentPreference(experience.tcf_purposes) ||
  hasCurrentPreference(experience.tcf_special_features) ||
  hasCurrentPreference(experience.tcf_vendors) ||
  hasCurrentPreference(experience.tcf_systems);

export const hasActionNeededTcfPreferences = (experience: PrivacyExperience) =>
  hasActionNeededTcfPreference(experience.tcf_purposes) ||
  hasActionNeededTcfPreference(experience.tcf_special_features) ||
  hasActionNeededTcfPreference(experience.tcf_vendors) ||
  hasActionNeededTcfPreference(experience.tcf_systems);

/**
 * Returns true if there are notices in the experience that require a user preference
 */
export const hasActionNeededNotices = (experience: PrivacyExperience) => {
  if (experience.component === ComponentType.TCF_OVERLAY) {
    return hasActionNeededTcfPreferences(experience);
  }
  return Boolean(
    experience?.privacy_notices?.some(
      (notice) => notice.current_preference == null
    )
  );
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

  if (!value) {
    return GpcStatus.APPLIED;
  }

  return GpcStatus.OVERRIDDEN;
};
