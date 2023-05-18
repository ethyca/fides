import {
  PrivacyExperience,
  PrivacyPreferencesCreateWithCode,
} from "~/lib/consent-types";
import { debugLog } from "../../lib/consent-utils";

/**
 * Fetch the relevant experience based on user location and user device id (if exists).
 * Fetches both Privacy Center and Overlay components, because GPC needs to work regardless of component
 */
export const getExperience = (
  userLocationString: String,
  debug: boolean
): PrivacyExperience | undefined => {
  debugLog(debug, "Fetching experience for location...", userLocationString);
  // TODO: GET /privacy-experience
  return undefined;
};

/**
 * Sends user consent preference downstream to Fides
 */
export const saveUserPreference = (
  userDeviceId: String,
  debug: boolean,
  preferences: PrivacyPreferencesCreateWithCode
): PrivacyExperience | undefined => {
  debugLog(
    debug,
    "Saving user consent preference for device id...",
    userDeviceId,
    preferences
  );
  // TODO: PATCH /consent-request/{consent_request_id}/privacy-preferences
  return undefined;
};
