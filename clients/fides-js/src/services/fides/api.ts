import {
  PrivacyExperience,
  PrivacyPreferencesRequest,
} from "~/lib/consent-types";
import { debugLog } from "../../lib/consent-utils";

/**
 * Fetch the relevant experience based on user location and user device id (if exists).
 * Fetches both Privacy Center and Overlay components, because GPC needs to work regardless of component
 */
export const fetchExperience = async (
    userLocationString: string,
    fidesApiUrl: string,
    fidesUserDeviceId: string,
    debug: boolean
): Promise<PrivacyExperience | {}> => {
  debugLog(debug, "Fetching experience for location...", userLocationString);
  const fetchOptions: RequestInit = {
    method: "GET",
    mode: "cors",
  };
  const response = await fetch(`${fidesApiUrl}/privacy-experience`, fetchOptions);
  if (!response.ok) {
    debugLog(
        debug,
        "Error getting experience from Fides API, returning {}. Response:",
        response
    );
    return {};
  }
  try {
    const body = await response.json();
    debugLog(
        debug,
        "Got experience response from Fides API, returning:",
        body
    );
    return body;
  } catch (e) {
    debugLog(
        debug,
        "Error parsing experience response body from Fides API, returning {}. Response:",
        response
    );
    return {};
  }
};

/**
 * Sends user consent preference downstream to Fides
 */
export const patchUserPreferenceToFidesServer = async (
    preferences: PrivacyPreferencesRequest,
    fidesApiUrl: string,
    fidesUserDeviceId: string,
    debug: boolean
): Promise<void> => {
  debugLog(debug, "Saving user consent preference...", preferences);
  const fetchOptions: RequestInit = {
    method: "PATCH",
    mode: "cors",
    body: JSON.stringify(preferences),
    headers: {
      "Content-Type": "application/json",
    }
  };
  const response = await fetch(`${fidesApiUrl}/privacy-preferences`, fetchOptions);
  if (!response.ok) {
    debugLog(
        debug,
        "Error patching user preference Fides API. Response:",
        response
    );
  }
  return Promise.resolve()
};
