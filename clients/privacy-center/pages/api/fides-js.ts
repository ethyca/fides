/* eslint-disable no-console */
import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";
import { CacheControl, stringify } from "cache-control-parser";

import { ConsentOption, FidesConfig } from "fides-js";
import { loadPrivacyCenterEnvironment } from "~/app/server-environment";

const FIDES_JS_MAX_AGE_SECONDS = 60 * 60; // one hour
const CLOUDFRONT_HEADER_COUNTRY = "cloudfront-viewer-country";
const CLOUDFRONT_HEADER_REGION = "cloudfront-viewer-region";

/**
 * Server-side API route to generate the customized "fides.js" script
 * based on the current configuration values.
 *
 * DEFER: Optimize this route, and ensure it is cacheable
 * (see https://github.com/ethyca/fides/issues/3170)
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // TODO: hoist these two "lookup location" blocks of logic to a helper function
  // Optionally, the caller can request a customized "fides.js" bundle for a
  // specific geo-location (e.g. "US-CA"). This location can be found in 3 ways:
  // 1) Providing a supported geo-location header (e.g. "Cloudfront-Viewer-Country: US")
  // 2) Providing an explicit "location" query param (e.g. /fides.js?location=US-CA)
  // 3) (future) Performing a geo-ip lookup for the request IP address
  let location: string | undefined;
  if (typeof req.headers[CLOUDFRONT_HEADER_COUNTRY] === "string") {
    location = req.headers[CLOUDFRONT_HEADER_COUNTRY].split(",")[0];
    if (typeof req.headers[CLOUDFRONT_HEADER_REGION] === "string") {
      location += "-" + req.headers[CLOUDFRONT_HEADER_COUNTRY].split(",")[0];
    }
  }

  // Check for any provided "geo-location" query params (optional)
  const { location: locationParam, country, region } = req.query;
  if (typeof locationParam === "string" && locationParam) {
    location = locationParam;
  } else if (typeof country === "string" && country) {
    location = country;
    if (typeof region === "string" && region) {
      location += "-" + region;
    }
  }
  
  // TODO: validate the location, slightly

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

  // Create the FidesConfig object that will be used to initialize fides.js
  const fidesConfig: FidesConfig & { location?: string } = {
    consent: {
      options,
    },
    location,
  };
  const fidesConfigJSON = JSON.stringify(fidesConfig);

  // DEFER: Optimize this by loading from a vendored asset folder instead
  // (see https://github.com/ethyca/fides/issues/3170)
  console.log(
    "Bundling generic fides.js & Privacy Center configuration together..."
  );
  const fidesJSBuffer = await fsPromises.readFile("../fides-js/dist/fides.js");
  const fidesJS: string = fidesJSBuffer.toString();
  if (!fidesJS || fidesJS === "") {
    throw new Error("Unable to load latest fides.js script from server!");
  }
  const script = `
  (function () {
    // Include generic fides.js script
    ${fidesJS}

    // Initialize fides.js with custom config
    var fidesConfig = ${fidesConfigJSON};
    window.Fides.init(fidesConfig);
  })();
  `;

  // Calculate the cache-control headers
  // TODO: ...configuration?
  const cacheHeaders: CacheControl = {
    "max-age": FIDES_JS_MAX_AGE_SECONDS,
    "public": true,
  };

  // Send the bundled script, ready to be loaded directly into a page!
  res
    .status(200)
    .setHeader("Content-Type", "application/javascript")
    .setHeader("Cache-Control", stringify(cacheHeaders))
    .send(script);
}
