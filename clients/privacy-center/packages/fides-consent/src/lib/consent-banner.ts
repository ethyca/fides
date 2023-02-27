import {
  CookieKeyConsent,
  hasSavedConsentCookie,
  setConsentCookieAcceptAll,
  setConsentCookieRejectAll,
} from "./cookie";

export type ConsentBannerOptions = {
  // Whether or not debug log statements should be enabled
  debug?: boolean

  // API URL to use for obtaining user geolocation. Must be provided if isGeolocationEnabled = true
  // Expects this API to accept a basic HTTP GET and return a UserGeolocation response, e.g.
  // ```bash
  // curl "https://example-geolocation.com/getlocation?api_key=123"
  // {"country":"US","ip":"192.168.0.1:1234","location":"US-NY","region":"NY"}
  // ```
  geolocationApiUrl?: string

  // Whether or not the banner should be globally disabled
  isDisabled?: boolean 

  // Whether user geolocation should be enabled. Requires geolocationApiUrl
  isGeolocationEnabled?: boolean

  // List of country codes where the banner should be enabled. Requires isGeolocationEnabled = true
  isEnabledCountries?: string[]

  // Display labels used for the banner text
  labels?: {
    bannerDescription?: string
    primaryButton?: string
    secondaryButton?: string
    tertiaryButton?: string
  }

  // URL for the Privacy Center, used to customize consent preferences. Required.
  privacyCenterUrl?: string
};

export type UserGeolocation = {
  country?: string  // "US"
  ip?: string // "192.168.0.1:12345"
  location?: string // "US-NY"
  region?: string // "NY"
}

// Adapted from https://gist.github.com/henrik/1688572?permalink_comment_id=4317520#gistcomment-4317520o
// (NOTE: Surprisingly, there's not really a list of these anywhere easily...?)
const EU_COUNTRY_CODES = [
  "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "HU",
  "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES",
  "SE", "UK",

  // ...plus some aliases that might occur (see https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Imperfect_implementations)
  "GB",
  "GR", 

  // ...plus EEA countries
  "CH",
  "IS",
  "LI",
  "NO",
];

/**
 * Configuration options used for the consent banner. The default values (below)
 * will be mutated by the banner() function to override with any user-provided
 * options at runtime.
 * 
 * This is effectively a global variable, but we provide getter/setter functions
 * to make it seem safer and only export the getBannerOptions() one outside this
 * module.
 */
let globalBannerOptions: ConsentBannerOptions = {
  debug: false,
  geolocationApiUrl: "http://localhost:3000/location", // TODO: default?
  isDisabled: false,
  isGeolocationEnabled: false,
  isEnabledCountries: EU_COUNTRY_CODES,
  labels: {
    bannerDescription: "This website processes your data respectfully, so we require your consent to use cookies.",
    primaryButton: "Accept All",
    secondaryButton: "Reject All",
    tertiaryButton: "Manage Preferences",
  },
  privacyCenterUrl: "http://localhost:3000" // TODO: default?
};

/**
 * Get the configured options for the consent banner 
 */
export const getBannerOptions = (): ConsentBannerOptions => globalBannerOptions;

/**
 * Wrapper around 'console.log' that only logs output when the 'debug' banner
 * option is truthy
 */
type ConsoleLogParameters = Parameters<typeof console.log>
const debugLog = (...args: ConsoleLogParameters): void => {
  if (getBannerOptions().debug) {
    // eslint-disable-next-line no-console
    console.log(...args) // TODO: use console.debug instead?
  }
};

/**
 * Change the consent banner options.
 * 
 * WARNING: If called after `banner()` has already ran, many of these options
 * will no longer take effect!
 */
const setBannerOptions = (options: ConsentBannerOptions): void => {
  globalBannerOptions = options;
};

/**
 * Validate the banner options. This checks for errors like using geolocation
 * without an API
 */
const validateBannerOptions = (options: ConsentBannerOptions): boolean => {
  // Check if options is an invalid type
  if (options === undefined || typeof options !== "object") {
    return false;
  }

  if (options.geolocationApiUrl) {
    try {
      // eslint-disable-next-line no-new
      new URL(options.geolocationApiUrl);
    } catch (e) {
      debugLog("Invalid banner options: geolocationApiUrl is an invalid URL!", options);
      return false;
    }
  }

  if (options.isGeolocationEnabled && !options.geolocationApiUrl) {
    debugLog("Invalid banner options: isGeolocationEnabled = true requires geolocationApiUrl!", options);
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
      debugLog("Invalid banner options: geolocationApiUrl is an invalid URL!", options);
      return false;
    }
  }

  return true;
}

/**
 * Navigates to the Fides Privacy Center to manage consent settings
 */
const navigateToPrivacyCenter = (): void => {
  const options: ConsentBannerOptions = getBannerOptions();
  debugLog("Navigate to Privacy Center URL:", options.privacyCenterUrl);
  if (options.privacyCenterUrl) {
    window.location.assign(options.privacyCenterUrl);
  }
}

/**
 * Fetch the user's geolocation from an external API
 */
const getLocation = async (): Promise<UserGeolocation> => {
  debugLog("Running getLocation...");
  const options = getBannerOptions();
  if (!options.geolocationApiUrl) {
    debugLog("Missing geolocationApiUrl, cannot get location!");
    return {};
  }

  debugLog(`Calling geolocation API: GET ${options.geolocationApiUrl}...`);
  const fetchOptions: RequestInit = {
    mode: "cors"
  };
  const response = await fetch(options.geolocationApiUrl,fetchOptions);

  if (!response.ok) {
    debugLog("Error getting location from geolocation API, returning {}. Response:", response);
    return {};
  }

  try {
    const body = await response.json();
    debugLog("Got location response from geolocation API, returning:", body);
    return body;
  } catch (e) {
    debugLog("Error parsing response body from geolocation API, returning {}. Response:", response);
    return {};
  }
}

/**
 * Determine whether or not the banner should be enabled for the given location
 */
const isBannerEnabledForLocation = (location?: UserGeolocation): boolean => {
  const options = getBannerOptions();
  if (location === undefined || !location) {
    debugLog("Location unknown, assume banner must be shown. isBannerEnabledForLocation = true");
    return true;
  }

  // Get the user's country
  if (location.country === undefined || !location.country) {
    debugLog("Country unknown, assume banner must be shown. isBannerEnabledForLocation = true");
    return true;
  }

  if (options.isEnabledCountries) {
    if (options.isEnabledCountries.includes(location.country)) {
      debugLog(`Country ${location.country} included in isEnabledCountries, banner must be shown. isBannerEnabledForLocation = true`);
      return true;
    }
    debugLog(`Country ${location.country} not included in isEnabledCountries, banner must be hidden. isBannerEnabledForLocation = false`);
    return false;
  }

  debugLog("No location-specific rules matched, assume banner must be shown. isBannerEnabledForLocation = true");
  return true;
}

/**
 * Builds a button DOM element with the given id, class name, and text label
 */
const buildButton = (id: string, className: string, label?: string, onClick?: (event: MouseEvent) => void): HTMLButtonElement => {
  const button = document.createElement("button");
  button.id = id;
  button.innerHTML = label || "";
  button.classList.add("fides-consent-banner-button");
  button.classList.add(className);
  button.addEventListener("click", (event) => {
    debugLog(`Fides consent banner button clicked with id='${id}'`);
    if (onClick !== undefined) {
      onClick(event);
    }
  });
  return button;
};

/**
 * Show the banner
 */
const showBanner = (banner: HTMLDivElement) => {
  banner.classList.remove("fides-consent-banner-hidden");
};

/**
 * Hide the banner (probably because the user selected a consent option)
 */
const hideBanner = (banner: HTMLDivElement) => {
  banner.classList.add("fides-consent-banner-hidden");
};

/**
 * Builds the DOM elements for the consent banner (container, buttons, etc.) and
 * return a single div that can be added to the body.
 */
const buildBanner = (defaults: CookieKeyConsent): HTMLDivElement => {
  const options: ConsentBannerOptions = getBannerOptions();

  // Create the overall banner container
  const banner = document.createElement("div");
  banner.id = "fides-consent-banner";
  banner.classList.add("fides-consent-banner");
  // TODO: support option to specify top/bottom
  banner.classList.add("fides-consent-banner-bottom");
  banner.classList.add("fides-consent-banner-hidden");

  // Add the banner description
  const bannerDescription = document.createElement("div");
  bannerDescription.id = "fides-consent-banner-description";
  bannerDescription.classList.add("fides-consent-banner-description");
  bannerDescription.innerText = options.labels?.bannerDescription || "";
  banner.appendChild(bannerDescription);

  // Create the button container
  const buttonContainer = document.createElement("div");
  buttonContainer.id = "fides-consent-banner-buttons";
  buttonContainer.classList.add("fides-consent-banner-buttons");

  // Create the banner buttons
  const tertiaryButton = buildButton(
    "fides-consent-banner-button-tertiary",
    "fides-consent-banner-button-tertiary",
    options.labels?.tertiaryButton,
    navigateToPrivacyCenter,
  );
  buttonContainer.appendChild(tertiaryButton);
  const secondaryButton = buildButton(
    "fides-consent-banner-button-secondary",
    "fides-consent-banner-button-secondary",
    options.labels?.secondaryButton,
    () => {
      setConsentCookieRejectAll(defaults);
      hideBanner(banner);
      // TODO: save to Fides consent request API
      // eslint-disable-next-line no-console
      console.error("Could not save consent record to Fides API, not implemented!");
    },
  );
  buttonContainer.appendChild(secondaryButton);
  const primaryButton = buildButton(
    "fides-consent-banner-button-primary",
    "fides-consent-banner-button-primary",
    options.labels?.primaryButton,
    () => {
      setConsentCookieAcceptAll(defaults);
      hideBanner(banner);
      // TODO: save to Fides consent request API
      // eslint-disable-next-line no-console
      console.error("Could not save consent record to Fides API, not implemented!");
    },
  );
  buttonContainer.appendChild(primaryButton);

  // Add the button container to the banner
  banner.appendChild(buttonContainer);

  return banner;
};

/**
 * Default CSS styles for the banner
 */
// TODO: move into a .css file and import
const globalBannerStyle = `
:root {
  --fides-consent-banner-font-family: inherit;
  --fides-consent-banner-font-size: 16px;
  --fides-consent-banner-background: #fff;
  --fides-consent-banner-text-color: #24292f;
  --fides-consent-banner-padding: 0.75em 2em 1em;

  --fides-consent-banner-button-background: #eee;
  --fides-consent-banner-button-text-color: #24292f;
  --fides-consent-banner-button-hover-background: #ccc;
  --fides-consent-banner-button-border-radius: 4px;
  --fides-consent-banner-button-padding: 1em 1.5em;

  --fides-consent-banner-button-primary-background: #464b83;
  --fides-consent-banner-button-primary-text-color: #fff;
  --fides-consent-banner-button-primary-hover-background: #3f4375;

  --fides-consent-banner-button-secondary-background: var(--fides-consent-banner-button-background);
  --fides-consent-banner-button-secondary-text-color: var(--fides-consent-banner-button-text-color);
  --fides-consent-banner-button-secondary-hover-background: var(--fides-consent-banner-button-hover-background);

  --fides-consent-banner-button-tertiary-background: var(--fides-consent-banner-button-background);
  --fides-consent-banner-button-tertiary-text-color: var(--fides-consent-banner-button-text-color);
  --fides-consent-banner-button-tertiary-hover-background: var(--fides-consent-banner-button-hover-background);
}

div#fides-consent-banner {
  font-family: var(--fides-consent-banner-font-family);
  font-size: var(--fides-consent-banner-font-size);
  background: var(--fides-consent-banner-background);
  color: var(--fides-consent-banner-text-color);
  box-sizing: border-box;
  padding: var(--fides-consent-banner-padding);

  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  transition: transform 1s;
}

div#fides-consent-banner.fides-consent-banner-bottom {
  position: fixed;
  z-index: 1;
  width: 100%;
  bottom: 0;
  left: 0;
  transform: translateY(0%);
}

div#fides-consent-banner.fides-consent-banner-bottom.fides-consent-banner-hidden {
  transform: translateY(100%);
}

div#fides-consent-banner.fides-consent-banner-top {
  position: fixed;
  z-index: 1;
  width: 100%;
  top: 0;
  left: 0;
  transform: translateY(0%);
}

div#fides-consent-banner.fides-consent-banner-top.fides-consent-banner-hidden {
  transform: translateY(-100%);
}


div#fides-consent-banner-description {
  margin-top: 0.5em;
  margin-right: 2em;
  min-width: 33%;
  flex: 1;
}

div#fides-consent-banner-buttons {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
}

button.fides-consent-banner-button {
  display: inline-block;
  flex: auto;
  cursor: pointer;
  text-align: center;
  margin: 0;
  margin-top: 0.25em;
  margin-right: 0.25em;
  padding: var(--fides-consent-banner-button-padding);
  background: var(--fides-consent-banner-button-background);
  color: var(--fides-consent-banner-button-text-color);
  border: none;
  border-radius: var(--fides-consent-banner-button-border-radius);

  font-family: inherit;
  font-size: 100%;
  line-height: 1.15;
  text-decoration: none;
}

button.fides-consent-banner-button:hover {
  background: var(--fides-consent-banner-button-hover-background);
}

button.fides-consent-banner-button.fides-consent-banner-button-primary {
  background: var(--fides-consent-banner-button-primary-background);
  color: var(--fides-consent-banner-button-primary-text-color);
}

button.fides-consent-banner-button.fides-consent-banner-button-primary:hover {
  background: var(--fides-consent-banner-button-primary-hover-background);
}

button.fides-consent-banner-button.fides-consent-banner-button-secondary {
  background: var(--fides-consent-banner-button-secondary-background);
  color: var(--fides-consent-banner-button-secondary-text-color);
}

button.fides-consent-banner-button.fides-consent-banner-button-secondary:hover {
  background: var(--fides-consent-banner-button-secondary-hover-background);
}

button.fides-consent-banner-button.fides-consent-banner-button-tertiary {
  background: var(--fides-consent-banner-button-tertiary-background);
  color: var(--fides-consent-banner-button-tertiary-text-color);
}

button.fides-consent-banner-button.fides-consent-banner-button-tertiary:hover {
  background: var(--fides-consent-banner-button-tertiary-hover-background);
}
`

/**
 * Builds a 'style' element containing the CSS styles for the consent banner
 */
const buildStyles = (): Node => {
  const style = document.createElement("style");
  style.innerHTML = globalBannerStyle;
  return style;
};

/**
 * Initialize the Fides Consent Banner, with optional extraOptions to override defaults.
 * 
 * (see the type definition of ConsentBannerOptions for what options are available)
 */
export const initBanner = async (defaults: CookieKeyConsent, extraOptions?: ConsentBannerOptions): Promise<void> => {
  // If the user provides any extra options, override the defaults
  debugLog("Initializing Fides consent banner with consent cookie defaults...", defaults);
  if (extraOptions !== undefined) {
    if (typeof extraOptions !== "object") {
      // eslint-disable-next-line no-console
      console.error("Invalid 'extraOptions' arg for Fides.banner(), ignoring", extraOptions);
    } else {
      setBannerOptions({ ...getBannerOptions(), ...extraOptions });
    }
  }
  const options: ConsentBannerOptions = getBannerOptions();

  debugLog("Validating Fides consent banner options...", options);
  if (!validateBannerOptions(options)) {
    return;
  }

  if (options.isDisabled) {
    debugLog("Fides consent banner is disabled, skipping banner initialization!");
    return;
  }

  if (hasSavedConsentCookie()) {
    debugLog("Fides consent cookie already exists, skipping banner initialization!");
    return;
  }

  debugLog("Fides consent banner is enabled and consent cookie does not exist. Continuing...");

  if (options.isGeolocationEnabled) {
    debugLog("Fides consent banner geolocation is enabled. Getting user location...");
    const location = await getLocation();

    debugLog("Checking if Fides consent banner should be displayed for location:", location);
    if (!isBannerEnabledForLocation(location)) {
      debugLog("Fides consent banner is not enabled for location, skipping banner initialization!");
      return;
    }
  } else {
    debugLog("Fides consent banner geolocation is not enabled. Continuing...");
  }

  debugLog("Fides consent banner should be shown! Building banner elements & styles...");
  const banner = buildBanner(defaults);
  const styles = buildStyles();

  debugLog("Adding Fides consent banner CSS & HTML into the DOM...");
  document.head.appendChild(styles);
  document.body.appendChild(banner);

  // Show the banner after a small delay, to allow animation to occur
  await setTimeout(() => showBanner(banner), 100);
  debugLog("Fides consent banner is now showing!");
};
