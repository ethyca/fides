/* eslint-disable no-console */
import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";
import { CacheControl, stringify } from "cache-control-parser";

import { ConsentOption, FidesConfig } from "fides-js";
import { loadPrivacyCenterEnvironment } from "~/app/server-environment";
import {
  getLocation,
  LOCATION_HEADERS,
  UserGeolocation,
} from "~/common/location";

const FIDES_JS_MAX_AGE_SECONDS = 60 * 60; // one hour

/**
 * Server-side API route to generate the customized "fides.js" script
 * based on the current configuration values.
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Check if a location was provided via headers or query param; if so, inject into the bundle
  const location = getLocation(req);

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
  // DEFER: update this to match what FidesConfig expects in the future for location
  const fidesConfig: FidesConfig & { location?: UserGeolocation } = {
    consent: {
      options,
    },
    options: {
      debug: true,
      isOverlayDisabled: true,
      isGeolocationEnabled: false,
      geolocationApiUrl: "",
      privacyCenterUrl: "http://localhost:3000",
    },
    location,
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
