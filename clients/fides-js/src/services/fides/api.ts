import {
  ComponentType,
  PrivacyExperience,
  PrivacyPreferencesRequest,
} from "../../lib/consent-types";
import { debugLog } from "../../lib/consent-utils";

export enum FidesEndpointPaths {
  PRIVACY_EXPERIENCE = "/privacy-experience",
  PRIVACY_PREFERENCES = "/privacy-preferences",
}

/**
 * Fetch the relevant experience based on user location and user device id (if exists).
 * Fetches both Privacy Center and Overlay components, because GPC needs to work regardless of component
 */
export const fetchExperience = async (
  userLocationString: string,
  fidesApiUrl: string,
  fidesUserDeviceId: string,
  debug: boolean
): Promise<PrivacyExperience | null> => {
  debugLog(
    debug,
    `Fetching experience for userId: ${fidesUserDeviceId} in location: ${userLocationString}`
  );
  const fetchOptions: RequestInit = {
    method: "GET",
    mode: "cors",
  };
  const params = new URLSearchParams({
    show_disabled: "false",
    region: userLocationString,
    component: ComponentType.OVERLAY,
    has_notices: "true",
    has_config: "true",
    fides_user_device_id: fidesUserDeviceId,
  });
  const response = await fetch(
    `${fidesApiUrl}${FidesEndpointPaths.PRIVACY_EXPERIENCE}?${params}`,
    fetchOptions
  );
  if (!response.ok) {
    debugLog(
      debug,
      "Error getting experience from Fides API, returning null. Response:",
      response
    );
    return null;
  }
  try {
    const body = await response.json();
    const experience = body.items && body.items[0];
    if (!experience) {
      debugLog(
        debug,
        "No relevant experience found from Fides API, returning null. Response:",
        body
      );
      return null;
    }
    debugLog(
      debug,
      "Got experience response from Fides API, returning:",
      experience
    );
    return experience;
  } catch (e) {
    debugLog(
      debug,
      "Error parsing experience response body from Fides API, returning {}. Response:",
      response
    );
    return null;
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
    },
  };
  const response = await fetch(
    `${fidesApiUrl}${FidesEndpointPaths.PRIVACY_PREFERENCES}`,
    fetchOptions
  );
  if (!response.ok) {
    debugLog(
      debug,
      "Error patching user preference Fides API. Response:",
      response
    );
  }
  return Promise.resolve();
};
