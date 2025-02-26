import { UserGeolocation } from "../../lib/consent-types";

/**
 * Fetch the user's geolocation from an external API
 */
export const getGeolocation = async (
  isGeolocationEnabled?: boolean,
  geolocationApiUrl?: string,
): Promise<UserGeolocation | null> => {
  fidesDebugger("Running getLocation...");

  if (!isGeolocationEnabled) {
    fidesDebugger(
      `User location could not be retrieved because geolocation is disabled.`,
    );
    return null;
  }

  if (!geolocationApiUrl) {
    fidesDebugger(
      "Location cannot be found due to no configured geoLocationApiUrl.",
    );
    return null;
  }

  fidesDebugger(`Calling geolocation API: GET ${geolocationApiUrl}...`);
  const fetchOptions: RequestInit = {
    mode: "cors",
  };
  const response = await fetch(geolocationApiUrl, fetchOptions);

  if (!response.ok) {
    fidesDebugger(
      "Error getting location from geolocation API, returning {}. Response:",
      response,
    );
    return null;
  }

  try {
    const body = await response.json();
    fidesDebugger(
      "Got location response from geolocation API, returning:",
      body,
    );
    return body;
  } catch (e) {
    fidesDebugger(
      "Error parsing response body from geolocation API, returning {}. Response:",
      response,
    );
    return null;
  }
};
