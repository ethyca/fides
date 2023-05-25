/* eslint-disable no-console */
import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";
import { CacheControl, stringify } from "cache-control-parser";

import { ConsentOption, FidesConfig } from "fides-js";
import { loadPrivacyCenterEnvironment } from "~/app/server-environment";
import { getGeolocation, LOCATION_HEADERS } from "~/common/geolocation";

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
  // Check if a geolocation was provided via headers or query param; if so, inject into the bundle
  const geolocation = getGeolocation(req);

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

  // Create the FidesConfig JSON that will be used to initialize fides.js
  const fidesConfig: FidesConfig = {
    consent: {
      options,
    },
    options: {
      debug: environment.settings.DEBUG,
      isOverlayDisabled: environment.settings.IS_OVERLAY_DISABLED,
      isGeolocationEnabled: environment.settings.IS_GEOLOCATION_ENABLED,
      geolocationApiUrl: environment.settings.GEOLOCATION_API_URL,
      privacyCenterUrl: environment.settings.PRIVACY_CENTER_URL,
    },
    geolocation,
  };
  const fidesConfigJSON = JSON.stringify(fidesConfig);

  console.log(
    "Bundling generic fides.js & Privacy Center configuration together..."
  );
  const fidesJSBuffer = await fsPromises.readFile("public/lib/fides.js");
  const fidesJS: string = fidesJSBuffer.toString();
  const fidesCSSBuffer = await fsPromises.readFile(
    "../fides-js/dist/fides.css"
  );
  const fidesCSS: string = JSON.stringify(fidesCSSBuffer.toString());
  if (!fidesJS || fidesJS === "") {
    throw new Error("Unable to load latest fides.js script from server!");
  }
  const script = `
  (function () {
    // Include default CSS
    const style = document.createElement('style');
    style.innerHTML = ${fidesCSS};
    document.head.append(style);

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
