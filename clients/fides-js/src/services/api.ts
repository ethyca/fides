import {
  ComponentType,
  EmptyExperience,
  FidesApiOptions,
  FidesOptions,
  LastServedConsentSchema,
  PrivacyExperience,
  PrivacyPreferencesRequest,
  RecordConsentServedRequest,
} from "../lib/consent-types";
import { debugLog } from "../lib/consent-utils";
import { FidesCookie } from "../lib/cookie";

export enum FidesEndpointPaths {
  PRIVACY_EXPERIENCE = "/privacy-experience",
  PRIVACY_PREFERENCES = "/privacy-preferences",
  NOTICES_SERVED = "/notices-served",
}

/**
 * Fetch the relevant experience based on user location and user device id (if exists).
 * Fetches both Privacy Center and Overlay components, because GPC needs to work regardless of component
 */
export const fetchExperience = async (
  userLocationString: string,
  fidesApiUrl: string,
  debug: boolean,
  apiOptions?: FidesApiOptions | null,
  fidesUserDeviceId?: string | null
): Promise<PrivacyExperience | EmptyExperience> => {
  debugLog(
    debug,
    `Fetching experience for userId: ${fidesUserDeviceId} in location: ${userLocationString}`
  );
  if (apiOptions?.getPrivacyExperienceFn) {
    debugLog(debug, "Calling custom fetch experience fn");
    try {
      return await apiOptions.getPrivacyExperienceFn(
        userLocationString,
        fidesUserDeviceId
      );
    } catch (e) {
      debugLog(
        debug,
        "Error fetching experience from custom API, returning {}. Error: ",
        e
      );
      return {};
    }
  }

  debugLog(debug, "Calling Fides GET experience API");
  const fetchOptions: RequestInit = {
    method: "GET",
    mode: "cors",
    headers: [["Unescape-Safestr", "true"]],
  };
  let params: any = {
    show_disabled: "false",
    region: userLocationString,
    component: ComponentType.OVERLAY,
    has_notices: "true",
    has_config: "true",
    systems_applicable: "true",
    include_gvl: "true",
    include_meta: "true",
  };
  if (fidesUserDeviceId) {
    params.fides_user_device_id = fidesUserDeviceId;
  }
  params = new URLSearchParams(params);
  const response = await fetch(
    `${fidesApiUrl}${FidesEndpointPaths.PRIVACY_EXPERIENCE}?${params}`,
    fetchOptions
  );
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
    // returning empty obj instead of undefined ensures we can properly cache on server-side for locations
    // that have no relevant experiences
    const experience = (body.items && body.items[0]) ?? {};
    debugLog(
      debug,
      "Got experience response from Fides API, returning: ",
      experience
    );
    return experience;
  } catch (e) {
    debugLog(
      debug,
      "Error parsing experience response body from Fides API, returning {}. Response:",
      response
    );
    return {};
  }
};

const PATCH_FETCH_OPTIONS: RequestInit = {
  method: "PATCH",
  mode: "cors",
  headers: {
    "Content-Type": "application/json",
  },
};

/**
 * Sends user consent preference downstream to Fides or custom API
 */
export const patchUserPreference = async (
  preferences: PrivacyPreferencesRequest,
  options: FidesOptions,
  cookie: FidesCookie,
  experience: PrivacyExperience
): Promise<void> => {
  debugLog(options.debug, "Saving user consent preference...", preferences);
  if (options.apiOptions?.savePreferencesFn) {
    debugLog(options.debug, "Calling custom save preferences fn");
    try {
      await options.apiOptions.savePreferencesFn(
        cookie.consent,
        cookie.fides_string,
        experience
      );
    } catch (e) {
      debugLog(
        options.debug,
        "Error saving preferences to custom API, continuing. Error: ",
        e
      );
      return Promise.reject(e);
    }
    return Promise.resolve();
  }
  debugLog(options.debug, "Calling Fides save preferences API");
  const fetchOptions: RequestInit = {
    ...PATCH_FETCH_OPTIONS,
    body: JSON.stringify(preferences),
  };
  const response = await fetch(
    `${options.fidesApiUrl}${FidesEndpointPaths.PRIVACY_PREFERENCES}`,
    fetchOptions
  );
  if (!response.ok) {
    debugLog(
      options.debug,
      "Error patching user preference Fides API. Response:",
      response
    );
  }
  return Promise.resolve();
};

export const patchNoticesServed = async ({
  request,
  options,
}: {
  request: RecordConsentServedRequest;
  options: FidesOptions;
}): Promise<Array<LastServedConsentSchema> | null> => {
  debugLog(options.debug, "Saving that notices were served...");
  if (options.apiOptions?.patchNoticesServedFn) {
    debugLog(options.debug, "Calling custom patch notices served fn");
    try {
      return await options.apiOptions.patchNoticesServedFn(request);
    } catch (e) {
      debugLog(
        options.debug,
        "Error patching notices served to custom API, continuing. Error: ",
        e
      );
      return null;
    }
  }
  debugLog(options.debug, "Calling Fides patch notices served API");
  const fetchOptions: RequestInit = {
    ...PATCH_FETCH_OPTIONS,
    body: JSON.stringify(request),
  };
  const response = await fetch(
    `${options.fidesApiUrl}${FidesEndpointPaths.NOTICES_SERVED}`,
    fetchOptions
  );
  if (!response.ok) {
    debugLog(
      options.debug,
      "Error patching notices served. Response:",
      response
    );
    return null;
  }
  return response.json();
};
