import {
  PrivacyExperience,
  PrivacyPreferencesCreateWithCode,
} from "~/lib/consent-types";
import { debugLog } from "../../lib/consent-utils";

/**
 * Fetch the relevant experience based on user location and user device id (if exists).
 * Fetches both Privacy Center and Overlay components, because GPC needs to work regardless of component
 */
export const fetchExperience = (
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
  preferences: PrivacyPreferencesCreateWithCode,
  debug: boolean
): PrivacyExperience | undefined => {
  debugLog(debug, "Saving user consent preference...", preferences);
  // TODO: PATCH /consent-request/{consent_request_id}/privacy-preferences
  return undefined;
};
