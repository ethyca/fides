import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";
import { CacheControl, stringify } from "cache-control-parser";

import {
  ConsentOption,
  FidesConfig,
  constructFidesRegionString,
  CONSENT_COOKIE_NAME,
  fetchExperience,
} from "fides-js";
import { loadPrivacyCenterEnvironment } from "~/app/server-environment";
import { lookupGeolocation, LOCATION_HEADERS } from "~/common/geolocation";

const FIDES_JS_MAX_AGE_SECONDS = 60 * 60; // one hour

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
    const fidesRegionString = constructFidesRegionString(geolocation);
    if (fidesRegionString) {
      if (environment.settings.DEBUG) {
        console.log("Fetching relevant experiences from server-side...");
      }
      experience = await fetchExperience(
        fidesRegionString,
        environment.settings.SERVER_SIDE_FIDES_API_URL ||
          environment.settings.FIDES_API_URL,
        "",
        environment.settings.DEBUG
      );
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
      serverSideFidesApiUrl:
        environment.settings.SERVER_SIDE_FIDES_API_URL ||
        environment.settings.FIDES_API_URL,
      tcfEnabled: environment.settings.TCF_ENABLED,
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
  const fidesJSBuffer = await fsPromises.readFile("public/lib/fides.js");
  const fidesJS: string = fidesJSBuffer.toString();
  if (!fidesJS || fidesJS === "") {
    throw new Error("Unable to load latest fides.js script from server!");
  }
  const script = `
  (function () {
    // This polyfill service adds a fetch polyfill only when needed, depending on browser making the request 
    var script = document.createElement('script');
    script.src = 'https://polyfill.io/v3/polyfill.min.js?features=fetch';
    document.head.appendChild(script);
    
    // Include generic fides.js script
    ${fidesJS}

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
