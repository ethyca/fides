import { h, render } from "preact";
import { CookieKeyConsent } from "./cookie";
import ConsentLink from "./consent-link";
import ConsentBanner from "./consent-banner";
import { ConsentBannerOptions, UserGeolocation } from "./consent-types";
import debugLog, {
  getBannerOptions,
  setBannerOptions,
} from "./consent-utils";

/**
 * Validate the banner options. This checks for errors like using geolocation
 * without an API
 */
const validateBannerOptions = (options: ConsentBannerOptions): boolean => {
  // Check if options is an invalid type
  if (options === undefined || typeof options !== "object") {
    return false;
  }

  if (typeof options.labels === "object") {
    let validLabels = true;
    Object.entries(options.labels).forEach((value: [string, string]) => {
      if (typeof value[1] !== "string") {
        debugLog(`Invalid banner options: labels.${value[0]} is not a string!`);
        validLabels = false;
      }
    });

    if (!validLabels) {
      return false;
    }
  }

  if (!options.privacyCenterUrl) {
    debugLog("Invalid banner options: privacyCenterUrl is required!");
    return false;
  }

  if (options.privacyCenterUrl) {
    try {
      // eslint-disable-next-line no-new
      new URL(options.privacyCenterUrl);
    } catch (e) {
      debugLog(
        "Invalid banner options: privacyCenterUrl is an invalid URL!",
        options
      );
      return false;
    }
  }

  return true;
};

/**
 * Fetch the user's geolocation from an external API
 */
const getLocation = async (): Promise<UserGeolocation> => {
  // assumes that isGeolocationEnabled is true
  debugLog("Running getLocation...");
  const options = getBannerOptions();
  const {geolocationApiUrl} = options

  if (!geolocationApiUrl) {
    debugLog(
        "Location cannot be found due to no configured geoLocationApiUrl."
    );
    return {};
  }

  debugLog(`Calling geolocation API: GET ${geolocationApiUrl}...`);
  const fetchOptions: RequestInit = {
    mode: "cors",
  };
  const response = await fetch(geolocationApiUrl, fetchOptions);

  if (!response.ok) {
    debugLog(
      "Error getting location from geolocation API, returning {}. Response:",
      response
    );
    return {};
  }

  try {
    const body = await response.json();
    debugLog("Got location response from geolocation API, returning:", body);
    return body;
  } catch (e) {
    debugLog(
      "Error parsing response body from geolocation API, returning {}. Response:",
      response
    );
    return {};
  }
};

/**
 * Determine applicable notices to be shown based on location
 */
const getApplicableNotices = (location?: UserGeolocation): any => {
  const options = getBannerOptions();
  // todo- call fides api with location to get applicable notices
  return {}
};

/**
 * Initialize the Fides Consent Banner or Link, with optional extraOptions to override defaults.
 *
 * (see the type definition of ConsentBannerOptions for what options are available)
 */
export const initFidesConsent = async (
  defaults: CookieKeyConsent,
  extraOptions?: ConsentBannerOptions
): Promise<void> => {
  debugLog(
    "Initializing Fides consent banner with consent cookie defaults...",
    defaults
  );
  if (extraOptions !== undefined) {
    if (typeof extraOptions !== "object") {
      // eslint-disable-next-line no-console
      console.error(
        "Invalid 'extraOptions' arg for Fides.banner(), ignoring",
        extraOptions
      );
    } else {
      // If the user provides any extra options, override the defaults
      setBannerOptions({ ...getBannerOptions(), ...extraOptions });
    }
  }
  const options: ConsentBannerOptions = getBannerOptions();

  debugLog("Validating Fides consent banner options...", options);
  if (!validateBannerOptions(options)) {
    return Promise.reject("Invalid banner options");
  }

  if (options.isDisabled) {
    debugLog(
      "Fides consent banner is disabled, skipping banner initialization!"
    );
    return Promise.reject("Banner is disabled");
  }


  document.addEventListener("DOMContentLoaded", (event) => {
    debugLog("DOM fully loaded and parsed");

    try {
      debugLog("Adding Fides consent banner CSS & HTML into the DOM...");
      if (options.isGeolocationEnabled) {
        getLocation().then((location) => {
          // todo- if location is {}, what notices do we render? all of them?
          const applicableNotices = getApplicableNotices(location)
        }).catch(() => {
          // if something goes wrong with location api, we still want to render notices
        })
      }
      render(
          <ConsentBanner defaults={defaults} options={options} waitBeforeShow={100}/>
        ,
        document.body
      );
      const consentLinkEl = document.getElementById("fides-consent-link");
      if (consentLinkEl !== null) {
        debugLog("Fides consent link el found");
        const consentLink = (
          <ConsentLink defaults={defaults} options={options} />
        );
        render(consentLink, consentLinkEl);
      } else {
        debugLog("Fides consent link el not found");
      }

      debugLog("Fides consent banner is now showing!");
    } catch (e) {
      debugLog(e);
    }
  });
};
