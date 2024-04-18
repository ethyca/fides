import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";
import { CacheControl, stringify } from "cache-control-parser";

import {
  ConsentOption,
  FidesConfig,
  constructFidesRegionString,
  fetchExperience,
  ComponentType,
} from "fides-js";
import { loadPrivacyCenterEnvironment } from "~/app/server-environment";
import { LOCATION_HEADERS, lookupGeolocation } from "~/common/geolocation";
import { safeLookupPropertyId } from "~/common/property-id";

// one hour, how long the client should cache fides.js for
const FIDES_JS_MAX_AGE_SECONDS = 60 * 60;
// one hour, how long until the custom-fides.css is refreshed
const CUSTOM_FIDES_CSS_TTL_MS = 3600 * 1000;

// a cache of the custom stylesheet retrieved from the /custom-asset endpoint
let cachedCustomFidesCss: string = "";
// millisecond timestamp of when the custom stylesheet was last retrieved
// used to determine when to refresh the contents
let lastFetched: number = 0;
// used to disable auto-refreshing if the /custom-asset endpoint is unreachable
let autoRefresh: boolean = true;

/**
 * @swagger
 * /fides.js:
 *   get:
 *     description: Generates a customized "fides.js" script bundle using the current configuration values
 *     parameters:
 *       - in: query
 *         name: geolocation
 *         required: false
 *         description: Geolocation string to inject into the bundle (e.g. "US-CA"), containing ISO 3166 country code (e.g. "US") and optional region code (e.g. "CA"), separated by a "-"
 *         schema:
 *           type: string
 *         example: US-CA
 *       - in: query
 *         name: property_id
 *         required: false
 *         description: Optional identifier used to filter for experiences associated with the given property. If omitted, returns all experiences not associated with any properties.
 *         schema:
 *           type: string
 *       - in: query
 *         name: refresh
 *         required: false
 *         description: Signals fides.js to use the latest custom-fides.css (if available)
 *         schema:
 *           type: boolean
 *       - in: header
 *         name: CloudFront-Viewer-Country
 *         required: false
 *         description: ISO 3166 country code to inject into the bundle
 *         schema:
 *           type: string
 *         example: US
 *       - in: header
 *         name: CloudFront-Viewer-Country-Region
 *         required: false
 *         description: ISO 3166 region code to inject into the bundle; requires CloudFront-Viewer-Country to also be present
 *         schema:
 *           type: string
 *         example: CA
 *     responses:
 *       200:
 *         description: Customized "fides.js" script bundle that is ready to insert into a website
 *         content:
 *           application/javascript:
 *             schema:
 *               type: string
 *             example: |
 *               (function(){
 *                 // fides.js bundle...
 *               )();
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Load the configured consent options (data uses, defaults, etc.) from environment
  const environment = await loadPrivacyCenterEnvironment();
  let options: ConsentOption[] = [];
  if (environment.config?.consent?.page.consentOptions) {
    const configuredOptions = environment.config.consent.page.consentOptions;
    options = configuredOptions.map((option) => ({
      fidesDataUseKey: option.fidesDataUseKey,
      default: option.default,
      cookieKeys: option.cookieKeys,
    }));
  }

  const fidesString = environment.settings.FIDES_STRING;

  // Check if a geolocation was provided via headers or query param
  const geolocation = await lookupGeolocation(req);

  const propertyId = safeLookupPropertyId(
    req,
    geolocation,
    environment,
    fidesString
  );

  // If a geolocation can be determined, "prefetch" the experience from the Fides API immediately.
  // This allows the bundle to be fully configured server-side, so that the Fides.js bundle can initialize instantly!

  let experience;
  if (
    geolocation &&
    environment.settings.IS_OVERLAY_ENABLED &&
    environment.settings.IS_PREFETCH_ENABLED &&
    !fidesString
  ) {
    const fidesRegionString = constructFidesRegionString(geolocation);

    if (fidesRegionString) {
      if (environment.settings.DEBUG) {
        // eslint-disable-next-line no-console
        console.log("Fetching relevant experiences from server-side...");
      }
      experience = await fetchExperience(
        fidesRegionString,
        environment.settings.SERVER_SIDE_FIDES_API_URL ||
          environment.settings.FIDES_API_URL,
        environment.settings.DEBUG,
        null,
        propertyId
      );
    }
  }

  // We determine server-side whether or not to send the TCF bundle, which is based
  // on whether or not the experience is marked as TCF. This means for TCF, we *must*
  // be able to prefetch the experience.
  const tcfEnabled = experience
    ? experience.experience_config?.component === ComponentType.TCF_OVERLAY
    : environment.settings.IS_FORCED_TCF;

  const gppEnabled = !!experience?.gpp_settings?.enabled;

  // Create the FidesConfig JSON that will be used to initialize fides.js
  const fidesConfig: FidesConfig = {
    consent: {
      options,
    },
    options: {
      debug: environment.settings.DEBUG,
      geolocationApiUrl: environment.settings.GEOLOCATION_API_URL,
      isGeolocationEnabled: environment.settings.IS_GEOLOCATION_ENABLED,
      isOverlayEnabled: environment.settings.IS_OVERLAY_ENABLED,
      isPrefetchEnabled: environment.settings.IS_PREFETCH_ENABLED,
      overlayParentId: environment.settings.OVERLAY_PARENT_ID,
      modalLinkId: environment.settings.MODAL_LINK_ID,
      privacyCenterUrl: environment.settings.PRIVACY_CENTER_URL,
      fidesApiUrl: environment.settings.FIDES_API_URL,
      tcfEnabled,
      serverSideFidesApiUrl:
        environment.settings.SERVER_SIDE_FIDES_API_URL ||
        environment.settings.FIDES_API_URL,
      fidesEmbed: environment.settings.FIDES_EMBED,
      fidesDisableSaveApi: environment.settings.FIDES_DISABLE_SAVE_API,
      fidesDisableBanner: environment.settings.FIDES_DISABLE_BANNER,
      fidesTcfGdprApplies: environment.settings.FIDES_TCF_GDPR_APPLIES,
      fidesString,
      // Custom API override functions must be passed into custom Fides extensions via Fides.init(...)
      apiOptions: null,
      fidesJsBaseUrl: environment.settings.FIDES_JS_BASE_URL,
      customOptionsPath: environment.settings.CUSTOM_OPTIONS_PATH,
      preventDismissal: environment.settings.PREVENT_DISMISSAL,
      allowHTMLDescription: environment.settings.ALLOW_HTML_DESCRIPTION,
      base64Cookie: environment.settings.BASE_64_COOKIE,
      fidesPrimaryColor: environment.settings.FIDES_PRIMARY_COLOR,
    },
    experience: experience || undefined,
    geolocation: geolocation || undefined,
  };
  const fidesConfigJSON = JSON.stringify(fidesConfig);

  if (process.env.NODE_ENV === "development") {
    // eslint-disable-next-line no-console
    console.log(
      "Bundling generic fides.js & Privacy Center configuration together..."
    );
  }
  const fidesJsFile = tcfEnabled
    ? "public/lib/fides-tcf.js"
    : "public/lib/fides.js";
  const fidesJSBuffer = await fsPromises.readFile(fidesJsFile);
  const fidesJS: string = fidesJSBuffer.toString();
  if (!fidesJS || fidesJS === "") {
    throw new Error("Unable to load latest fides.js script from server!");
  }
  let fidesGPP: string = "";
  if (gppEnabled) {
    // eslint-disable-next-line no-console
    console.log("GPP extension enabled, bundling fides-ext-gpp.js...");
    const fidesGPPBuffer = await fsPromises.readFile(
      "public/lib/fides-ext-gpp.js"
    );
    fidesGPP = fidesGPPBuffer.toString();
    if (!fidesGPP || fidesGPP === "") {
      throw new Error("Unable to load latest gpp extension from server!");
    }
  }

  /* eslint-disable @typescript-eslint/no-use-before-define */
  const customFidesCss = await fetchCustomFidesCss(req);

  const script = `
  (function () {
    // This polyfill service adds a fetch polyfill only when needed, depending on browser making the request
    if (!window.fetch) {
      var script = document.createElement('script');
      script.src = 'https://polyfill.io/v3/polyfill.min.js?features=fetch';
      document.head.appendChild(script);
    }

    // Include generic fides.js script
    ${fidesJS}${fidesGPP}${
    customFidesCss
      ? `
    // Include custom fides.css styles
    const style = document.createElement('style');
    style.innerHTML = ${JSON.stringify(customFidesCss)};
    document.head.append(style);
    `
      : ""
  }
    // Initialize fides.js with custom config
    var fidesConfig = ${fidesConfigJSON};
    window.Fides.init(fidesConfig);
  })();
  `;

  // Instruct any caches to store this response, since these bundles do not change often
  const cacheHeaders: CacheControl = {
    "max-age": FIDES_JS_MAX_AGE_SECONDS,
    public: true,
  };

  // Send the bundled script, ready to be loaded directly into a page!
  res
    .status(200)
    .setHeader("Content-Type", "application/javascript")
    // Allow CORS since this is a static file we do not need to lock down
    .setHeader("Access-Control-Allow-Origin", "*")
    .setHeader("Cache-Control", stringify(cacheHeaders))
    .setHeader("Vary", LOCATION_HEADERS)
    .send(script);
}

async function fetchCustomFidesCss(
  req: NextApiRequest
): Promise<string | null> {
  const currentTime = Date.now();
  const forceRefresh = "refresh" in req.query;

  // no cached value or TTL has elapsed
  const isCacheInvalid =
    !cachedCustomFidesCss ||
    (lastFetched && currentTime - lastFetched > CUSTOM_FIDES_CSS_TTL_MS);
  // refresh if forced or auto-refresh is enabled and the cache is invalid
  const shouldRefresh = forceRefresh || (autoRefresh && isCacheInvalid);

  if (shouldRefresh) {
    try {
      const environment = await loadPrivacyCenterEnvironment();
      const fidesUrl =
        environment.settings.SERVER_SIDE_FIDES_API_URL ||
        environment.settings.FIDES_API_URL;
      const response = await fetch(
        `${fidesUrl}/plus/custom-asset/custom-fides.css`
      );
      const data = await response.text();

      if (!response.ok) {
        // eslint-disable-next-line no-console
        console.error(
          "Error fetching custom-fides.css:",
          response.status,
          response.statusText,
          data
        );
        throw new Error(`HTTP error occurred. Status: ${response.status}`);
      }

      if (!data) {
        throw new Error("No data returned by the server");
      }

      // eslint-disable-next-line no-console
      console.log("Successfully retrieved custom-fides.css");
      autoRefresh = true;
      cachedCustomFidesCss = data;
      lastFetched = currentTime;
    } catch (error) {
      autoRefresh = false; // /custom-asset endpoint unreachable stop auto-refresh
      if (error instanceof Error) {
        // eslint-disable-next-line no-console
        console.error("Error during fetch operation:", error.message);
      } else {
        // eslint-disable-next-line no-console
        console.error("Unknown error occurred:", error);
      }
    }
  }
  return cachedCustomFidesCss;
}
