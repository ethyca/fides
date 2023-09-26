import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";
import { CacheControl, stringify } from "cache-control-parser";

import {
  ConsentOption,
  FidesConfig,
  constructFidesRegionString,
  fetchExperience,
} from "fides-js";
import { loadPrivacyCenterEnvironment } from "~/app/server-environment";
import { LOCATION_HEADERS, lookupGeolocation } from "~/common/geolocation";

// one hour, how long the client should cache fides.js for
const FIDES_JS_MAX_AGE_SECONDS = 60 * 60;
// one hour, how long until the custom-fides.css is refreshed
const CUSTOM_FIDES_CSS_TTL_MS = 3600 * 1000;

let cachedCustomFidesCss: string = "";
let lastFetched: number = 0;

async function fetchCustomFidesCss(
  req: NextApiRequest
): Promise<string | null> {
  const currentTime = Date.now();
  const shouldRefresh = "refresh" in req.query;
  if (
    !cachedCustomFidesCss ||
    (lastFetched && currentTime - lastFetched > CUSTOM_FIDES_CSS_TTL_MS) ||
    shouldRefresh
  ) {
    try {
      const environment = await loadPrivacyCenterEnvironment();
      const fidesUrl =
        environment.settings.SERVER_SIDE_FIDES_API_URL ||
        environment.settings.FIDES_API_URL;
      const response = await fetch(
        `${fidesUrl}/plus/custom-asset/custom-fides.css`
      );
      const data = await response.text();

      console.log("Successfully retrieved custom-fides.css");

      if (!response.ok) {
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

      cachedCustomFidesCss = data;
      lastFetched = currentTime;
    } catch (error) {
      if (error instanceof Error) {
        console.error("Error during fetch operation:", error.message);
      } else {
        console.error("Unknown error occurred:", error);
      }
    }
  }
  return cachedCustomFidesCss;
}

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

  // DEFER: The Fides server controls whether or not TCF is enabled, and so we
  // should prefetch that value here. Until the endpoint is ready, we use an
  // environment variable
  const tcfEnabled = environment.settings.TCF_ENABLED;

  // Check if a geolocation was provided via headers or query param
  const geolocation = await lookupGeolocation(req);

  // If a geolocation can be determined, "prefetch" the experience from the Fides API immediately.
  // This allows the bundle to be fully configured server-side, so that the Fides.js bundle can initialize instantly!

  let experience;
  if (
    geolocation &&
    environment.settings.IS_OVERLAY_ENABLED &&
    environment.settings.IS_PREFETCH_ENABLED
  ) {
    if (tcfEnabled) {
      // eslint-disable-next-line no-console
      console.warn(
        "TCF mode is not currently compatible with prefetching, skipping prefetching..."
      );
    } else {
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
          null
        );
      }
    }
  }

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
    ${fidesJS}

    // Include custom-fides.css
    const style = document.createElement('style');
    style.innerHTML = ${JSON.stringify(customFidesCss)};
    document.head.append(style);

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
    .setHeader("Cache-Control", stringify(cacheHeaders))
    .setHeader("Vary", LOCATION_HEADERS)
    .send(script);
}
