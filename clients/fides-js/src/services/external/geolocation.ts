import { UserGeolocation } from "../../lib/consent-types";
import { debugLog } from "../../lib/consent-utils";

/**
 * Fetch the user's geolocation from an external API
 */
export const getGeolocation = async (
  isGeolocationEnabled?: boolean,
  geolocationApiUrl?: string,
  forwarded_ip_info?: string | null,
  debug: boolean = false
): Promise<UserGeolocation | null> => {
  debugLog(debug, "Running getLocation...");

  if (!isGeolocationEnabled) {
    debugLog(
      debug,
      `User location could not be retrieved because geolocation is disabled.`
    );
    return null;
  }

  if (!geolocationApiUrl) {
    debugLog(
      debug,
      "Location cannot be found due to no configured geoLocationApiUrl."
    );
    return null;
  }

  debugLog(debug, `Calling geolocation API: GET ${geolocationApiUrl}...`);
  const fetchOptions: RequestInit = {
    mode: "cors",
  };
  if (forwarded_ip_info) {
    const headers: Headers = new Headers();
    headers.set("X-Forwarded-For", forwarded_ip_info)
    fetchOptions.headers = headers
  }
  const response = await fetch(geolocationApiUrl, fetchOptions);

  if (!response.ok) {
    debugLog(
      debug,
      "Error getting location from geolocation API, returning {}. Response:",
      response
    );
    return null;
  }

  try {
    const body = await response.json();
    debugLog(
      debug,
      "Got location response from geolocation API, returning:",
      body
    );
    return body;
  } catch (e) {
    debugLog(
      debug,
      "Error parsing response body from geolocation API, returning {}. Response:",
      response
    );
    return null;
  }
};
