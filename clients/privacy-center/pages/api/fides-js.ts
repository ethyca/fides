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
import { debugLog } from "~/common/logger";
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
  /**
   * Step 1: Load the server environment, including all settings from ENV
   * variables, legacy config.json options, etc.
   */
  const environment = await loadPrivacyCenterEnvironment();

  /**
   * Step 2: Initialize our debugging log context, which we use to provide
   * consistent traces when troubleshooting.
   */
  const logContext: any = {
    req,
    res,
    isOverlayEnabled: environment.settings.IS_OVERLAY_ENABLED,
    isPrefetchEnabled: environment.settings.IS_PREFETCH_ENABLED,
    geolocation: null,
    propertyId: null,
    isExperiencePrefetched: false,
    experienceConfigName: null,
    experienceConfigComponent: null,
    isTcfEnabled: false,
    isGppEnabled: false,
    isCustomCSSIncluded: false,
  };
  debugLog("/fides.js started handling request", logContext);

  /**
   * Step 3: Parse any "legacy" consent options from the config.json, which are
   * loaded into the fides.js bundle as defaults
   */
  let options: ConsentOption[] = [];
  if (environment.config?.consent?.page.consentOptions) {
    const configuredOptions = environment.config.consent.page.consentOptions;
    options = configuredOptions.map((option) => ({
      fidesDataUseKey: option.fidesDataUseKey,
      default: option.default,
      cookieKeys: option.cookieKeys,
    }));
  }

  /**
   * Step 4: Lookup the geolocation for the request, if provided via CloudFront
   * headers or the "geolocation" query param
   */
  const geolocation = await lookupGeolocation(req);
  logContext.geolocation = geolocation;
  debugLog(
    `/fides.js geolocation lookup finished (geolocation=${JSON.stringify(
      geolocation
    )})})`,
    logContext
  );

  // Check to see if a fidesString should be overriden for all fides.js bundles
  // DEFER: Remove this custom setting, it's dangerous!
  const fidesString = environment.settings.FIDES_STRING;

  /**
   * Step 5: Lookup the propertyId for the request, if provided with the
   * "property_id" query param
   *
   * NOTE: This is a "safe" lookup that will throw errors if a propertyId is
   * provided but a server-side fetch cannot be supported (e.g. no geolocation)
   */
  const propertyId = safeLookupPropertyId(
    req,
    geolocation,
    environment,
    fidesString
  );
  logContext.propertyId = propertyId;
  debugLog(
    `/fides.js propertyId lookup finished (propertyId=${JSON.stringify(
      propertyId
    )})`,
    logContext
  );

  /**
   * Step 6: Try to "prefetch" the experience for this request from the Fides
   * API server-side. This allows the experience to be preloaded into the
   * fides.js bundle in the response so it can initialize instantly!
   */
  let experience;
  if (
    geolocation &&
    environment.settings.IS_OVERLAY_ENABLED &&
    environment.settings.IS_PREFETCH_ENABLED &&
    !fidesString
  ) {
    const fidesRegionString = constructFidesRegionString(geolocation);

    if (fidesRegionString) {
      debugLog(
        `/fides.js pre-fetching experience server-side from Fides API (region=${fidesRegionString} and property_id=${propertyId})...`,
        logContext
      );
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

  // Update our logger context so it's clear if a server-side experience succeeded
  logContext.isExperiencePrefetched = Boolean(experience);
  logContext.experienceConfigName = experience?.experience_config?.name;
  logContext.experienceConfigComponent =
    experience?.experience_config?.component;
  debugLog(
    `/fides.js experience lookup finished (isExperiencePrefetched=${logContext.isExperiencePrefetched}, experienceConfigName=${logContext.experienceConfigName})`,
    logContext
  );

  // These query params are used for testing purposes only, and should not be used
  // in production. They allow for the config to be injected by the test framework
  // and delay the initialization of fides.js until the test framework is ready.
  const { e2e: e2eQuery, tcf: tcfQuery } = req.query;

  /**
   * Step 7: Enable TCF in the fides.js bundle, if needed.
   *
   * We *have* to determine whether or not to send the TCF bundle server-side,
   * since we need to serve different JavaScript files. Therefore, for TCF, we
   * *must* be able to prefetch the experience successfully above.
   *
   * If an experience cannot be prefetched, TCF can also be enabled with the
   * "tcf" query param, or by the IS_FORCED_TCF server setting.
   */
  const tcfEnabled =
    tcfQuery === "true" ||
    (experience
      ? experience.experience_config?.component === ComponentType.TCF_OVERLAY
      : environment.settings.IS_FORCED_TCF);
  logContext.isTcfEnabled = tcfEnabled;
  debugLog(
    `/fides.js TCF configuration finished (isTcfEnabled=${logContext.isTcfEnabled})`,
    logContext
  );

  /**
   * Step 8: Enable GPP in the fides.js bundle, if needed.
   *
   * Similar to TCF, this is based on the prefetched experience, or by providing
   * the "gpp" query param in the request.
   *
   */
  const { gpp: forcedGppQuery } = req.query;
  if (forcedGppQuery === "true" && experience === undefined) {
    experience = {};
  }
  const gppEnabled =
    !!experience?.gpp_settings?.enabled || forcedGppQuery === "true";
  logContext.isGppEnabled = gppEnabled;
  debugLog(
    `/fides.js GPP configuration finished (isGppEnabled=${logContext.isGppEnabled})`,
    logContext
  );

  /**
   * Step 9: Create the FidesConfig JSON that will be used to initialize fides.js.
   *
   * NOTE: This config object will be discarded if the "e2e" query param is
   * provided, so that E2E tests can inject their own configuration (see below)
   */
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
      fidesClearCookie: environment.settings.FIDES_CLEAR_COOKIE,
    },
    experience: experience || undefined,
    geolocation: geolocation || undefined,
  };
  const fidesConfigJSON = JSON.stringify(fidesConfig);

  /**
   * Step 10: Start building the fides.js bundle for this request by loading the
   * necessary JavaScript files from public/lib/...
   */
  debugLog(
    "/fides.js finished setup, start bundling fides.js, extensions, and configuration together...",
    logContext
  );
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
    debugLog(
      `/fides.js bundling fides-ext-gpp.js extension (GPP was ${
        forcedGppQuery === "true" ? "forced" : "enabled"
      })...`,
      logContext
    );
    const fidesGPPBuffer = await fsPromises.readFile(
      "public/lib/fides-ext-gpp.js"
    );
    fidesGPP = fidesGPPBuffer.toString();
    if (!fidesGPP || fidesGPP === "") {
      throw new Error("Unable to load latest gpp extension from server!");
    }
  }

  /**
   * Step 11: Fetch any custom CSS stylesheet from the Fides API to be included
   */
  /* eslint-disable @typescript-eslint/no-use-before-define */
  const customFidesCss = await fetchCustomFidesCss(req);
  logContext.isCustomCSSIncluded = Boolean(customFidesCss);
  debugLog(
    `/fides.js custom CSS lookup finished (isCustomCSSIncluded=${logContext.isCustomCSSIncluded})`,
    logContext
  );

  /**
   * Step 12: Create the fides.js bundle! This is as simple as some basic string
   * concatenation, with the entire contents of the module wrapped in a IIFE
   * (immediately-invoked-function-expression) so it is ready to be executed in
   * the user's browser
   */
  const script = `
  (function () {
    // This polyfill service adds a fetch polyfill only when needed, depending on browser making the request
    if (!window.fetch) {
      var script = document.createElement('script');
      script.src = 'https://polyfill.io/v3/polyfill.min.js?features=fetch';
      document.head.appendChild(script);
    }

    // Include generic fides.js script and GPP extension (if enabled)
    ${fidesJS}${fidesGPP}${
    customFidesCss
      ? `
    // Include custom fides.css styles
    const style = document.createElement('style');
    style.innerHTML = ${JSON.stringify(customFidesCss)};
    document.head.append(style);
    `
      : ""
  }${
    e2eQuery === "true"
      ? ""
      : `
        // Initialize fides.js with custom config
    var fidesConfig = ${fidesConfigJSON};
    window.Fides.init(fidesConfig);`
  }
  })();
  `;

  /**
   * Step 12: Send the completed fides.js bundle to the user, ready to be loaded
   * directly into a page!
   *
   * Note that we set relevant Cache-Control directives to instruct caches to
   * store this response, since these bundles do not change often. We also set
   * the "Vary" header with the CloudFront geolocation headers, to instruct
   * caches to store different responses for different geolocations, since the
   * bundles are expected to be different for different locations.
   */
  const cacheHeaders: CacheControl = {
    "max-age": FIDES_JS_MAX_AGE_SECONDS,
    public: true,
  };
  res
    .status(200)
    .setHeader("Content-Type", "application/javascript")
    // Allow CORS since this is a static file we do not need to lock down
    .setHeader("Access-Control-Allow-Origin", "*")
    .setHeader("Cache-Control", stringify(cacheHeaders))
    .setHeader("Vary", LOCATION_HEADERS)
    .send(script);
  debugLog(
    `/fides.js response complete! (statusCode=${res.statusCode})`,
    logContext
  );
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
