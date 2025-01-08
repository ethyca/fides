import { CacheControl, stringify } from "cache-control-parser";
import {
  ComponentType,
  ConsentOption,
  constructFidesRegionString,
  DEFAULT_LOCALE,
  EmptyExperience,
  fetchExperience,
  FidesConfig,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  UserGeolocation,
} from "fides-js";
import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";

import {
  loadPrivacyCenterEnvironment,
  loadServerSettings,
} from "~/app/server-environment";
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
 *         description: |
 *           Override FidesJS to use a specific geolocation by providing a valid [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2) code:
 *           1. Starts with a 2 letter country code (e.g. "US", "GB") (see [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2))
 *           2. (Optional) Ends with a 1-3 alphanumeric character region code (e.g. "CA", "123", "X") (see [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2))
 *           3. Country & region codes must be separated by a hyphen (e.g. "US-CA")
 *
 *           Fides also supports a special `EEA` geolocation code to denote the European Economic Area; this is not part of ISO 3166-2, but is supported for convenience.
 *         schema:
 *           type: string
 *         example: US-CA
 *       - in: query
 *         name: property_id
 *         required: false
 *         description: Optional identifier used to filter for experiences associated with the given property. If omitted, returns all experiences not associated with any properties.
 *         schema:
 *           type: string
 *         example: FDS-A0B1C2
 *       - in: query
 *         name: refresh
 *         required: false
 *         description: Signals fides.js to use the latest custom-fides.css (if available)
 *         schema:
 *           type: boolean
 *       - in: query
 *         name: gpp
 *         required: false
 *         description: Forces the GPP extension to be included in the bundle, even if the experience does not have GPP enabled
 *         schema:
 *           type: boolean
 *       - in: query
 *         name: initialize
 *         required: false
 *         description: When set to "false" fides.js will not be initialized automatically; use `window.Fides.init()` to initialize manually
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
  res: NextApiResponse,
) {
  // Load the configured consent options (data uses, defaults, etc.) from environment
  const environment = await loadPrivacyCenterEnvironment();
  const serverSettings = await loadServerSettings();

  let options: ConsentOption[] = [];
  if (environment.config?.consent?.page.consentOptions) {
    const configuredOptions = environment.config.consent.page.consentOptions;
    options = configuredOptions.map((option) => ({
      fidesDataUseKey: option.fidesDataUseKey,
      default: option.default!,
      cookieKeys: option.cookieKeys!,
    }));
  }

  const fidesString = environment.settings.FIDES_STRING;

  let geolocation: UserGeolocation | null;
  let propertyId: string | undefined;

  try {
    // Check if a geolocation was provided via headers or query param
    geolocation = await lookupGeolocation(req);

    propertyId = safeLookupPropertyId(
      req,
      geolocation,
      environment,
      fidesString,
    );
  } catch (error) {
    fidesError(error);
    res
      .status(400) // 400 Bad Request. Malformed request.
      .send(
        error instanceof Error ? error.message : "An unknown error occurred.",
      );
    return;
  }

  /**
   * NOTE: initializing `experience` as an empty object `{}` causes problems, specifically
   * for clients not using prefetch and CDNs as Fides.js interprets that as a valid, albeit
   * empty, experience and then does not make a follow up call to the `privacy-experience` API.
   * This is why we initialize `experience` as `undefined`.
   */
  let experience:
    | PrivacyExperience
    | PrivacyExperienceMinimal
    | EmptyExperience
    | undefined;

  // If a geolocation can be determined, "prefetch" the experience from the Fides API immediately.
  // This allows the bundle to be fully configured server-side, so that the Fides.js bundle can initialize instantly!

  if (
    geolocation &&
    environment.settings.IS_OVERLAY_ENABLED &&
    environment.settings.IS_PREFETCH_ENABLED &&
    !fidesString
  ) {
    const fidesRegionString = constructFidesRegionString(geolocation);

    if (fidesRegionString) {
      // Check for a provided "fides_locale" query param or cookie. If present, use it as
      // the user's preferred language, otherwise use the "accept-language" header
      // provided by the browser. If all else fails, use the default ("en").
      const fidesLocale =
        (req.query.fides_locale as string) || req.cookies?.fides_locale;
      const userLanguageString =
        fidesLocale || req.headers["accept-language"] || DEFAULT_LOCALE;

      fidesDebugger(
        `Fetching relevant experiences from server-side (${userLanguageString})...`,
      );

      /*
       * Since we don't know what the experience will be when the initial call is made,
       * we supply the minimal request to the api endpoint with the understanding that if
       * TCF is being returned, we want the minimal version. It will be ignored otherwise.
       */
      experience = await fetchExperience({
        userLocationString: fidesRegionString,
        userLanguageString,
        fidesApiUrl:
          serverSettings.SERVER_SIDE_FIDES_API_URL ||
          environment.settings.FIDES_API_URL,
        propertyId,
        requestMinimalTCF: true,
      });
    }
  }

  if (!geolocation) {
    fidesDebugger("No geolocation found, unable to prefetch experience.");
  }

  // This query param is used for testing purposes only, and should not be used
  // in production.
  const { tcf: tcfQuery } = req.query;

  // We determine server-side whether or not to send the TCF bundle, which is based
  // on whether or not the experience is marked as TCF. This means for TCF, we *must*
  // be able to prefetch the experience. This can also be forced via query param for
  // internal testing when we know the experience will be injected by the test framework.
  const tcfEnabled =
    tcfQuery === "true" ||
    (experience
      ? experience.experience_config?.component === ComponentType.TCF_OVERLAY
      : environment.settings.IS_FORCED_TCF);

  // Check for a provided "gpp" query param.
  // If the experience has GPP enabled, or the query param is present,
  // include the GPP extension in the bundle.
  const { gpp: forcedGppQuery } = req.query;
  if (forcedGppQuery === "true" && experience === undefined) {
    experience = {};
  }
  const gppEnabled =
    !!experience?.gpp_settings?.enabled || forcedGppQuery === "true";

  // Create the FidesConfig JSON that will be used to initialize fides.js unless in E2E mode (see below)
  const fidesConfig: FidesConfig = {
    consent: {
      options,
    },
    options: {
      debug: environment.settings.DEBUG || req.query.debug === "true",
      geolocationApiUrl: environment.settings.GEOLOCATION_API_URL,
      isGeolocationEnabled: environment.settings.IS_GEOLOCATION_ENABLED,
      isOverlayEnabled: environment.settings.IS_OVERLAY_ENABLED,
      isPrefetchEnabled: environment.settings.IS_PREFETCH_ENABLED,
      overlayParentId: environment.settings.OVERLAY_PARENT_ID,
      modalLinkId: environment.settings.MODAL_LINK_ID,
      privacyCenterUrl: environment.settings.PRIVACY_CENTER_URL,
      fidesApiUrl: environment.settings.FIDES_API_URL,
      tcfEnabled,
      gppEnabled,
      fidesEmbed: environment.settings.FIDES_EMBED,
      fidesDisableSaveApi: environment.settings.FIDES_DISABLE_SAVE_API,
      fidesDisableNoticesServedApi:
        environment.settings.FIDES_DISABLE_NOTICES_SERVED_API,
      fidesDisableBanner: environment.settings.FIDES_DISABLE_BANNER,
      fidesTcfGdprApplies: environment.settings.FIDES_TCF_GDPR_APPLIES,
      showFidesBrandLink: environment.settings.SHOW_BRAND_LINK,
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
      fidesConsentOverride: environment.settings.FIDES_CONSENT_OVERRIDE,
    },
    experience: experience || undefined,
    geolocation: geolocation || undefined,
    propertyId: propertyId || undefined,
  };
  const fidesConfigJSON = JSON.stringify(fidesConfig);

  fidesDebugger(
    "Bundling generic fides.js & Privacy Center configuration together...",
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
    fidesDebugger(
      `GPP extension ${
        forcedGppQuery === "true" ? "forced" : "enabled"
      }, bundling fides-ext-gpp.js...`,
    );
    const fidesGPPBuffer = await fsPromises.readFile(
      "public/lib/fides-ext-gpp.js",
    );
    fidesGPP = fidesGPPBuffer.toString();
    if (!fidesGPP || fidesGPP === "") {
      throw new Error("Unable to load latest gpp extension from server!");
    }
  }

  /* eslint-disable @typescript-eslint/no-use-before-define */
  const customFidesCss = await fetchCustomFidesCss(req);

  // Check if the client wants to skip initialization of fides.js to allow for manual initialization
  const { initialize: initializeQuery } = req.query;
  const skipInitialization = initializeQuery === "false";

  // keep fidesJS on the first line to avoid sourcemap issues!
  const script = `(function () {${fidesJS}
  ${fidesGPP}
  ${
    customFidesCss
      ? `// Include custom fides.css styles
    const style = document.createElement('style');
    style.innerHTML = ${JSON.stringify(customFidesCss)};
    document.head.append(style);`
      : ""
  }
  window.Fides.config = ${fidesConfigJSON};
  ${skipInitialization ? "" : `window.Fides.init();`}
  ${
    environment.settings.DEBUG && skipInitialization
      ? `console.log("Fides initialization skipped. Call window.Fides.init() manually.");`
      : ""
  }
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
    // Ignore cache if user's geolocation or language changes
    .setHeader("Vary", [...LOCATION_HEADERS, "Accept-Language"])
    .send(script);
}

async function fetchCustomFidesCss(
  req: NextApiRequest,
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
      const serverSettings = await loadServerSettings();

      const fidesUrl =
        serverSettings.SERVER_SIDE_FIDES_API_URL ||
        environment.settings.FIDES_API_URL;
      const response = await fetch(
        `${fidesUrl}/plus/custom-asset/custom-fides.css`,
      );
      const data = await response.text();

      if (!response.ok) {
        if (response.status === 404) {
          fidesDebugger("No custom-fides.css found, skipping...");
          autoRefresh = false;
          return null;
        }
        fidesError(
          "Error fetching custom-fides.css:",
          response.status,
          response.statusText,
          data,
        );
        throw new Error(`HTTP error occurred. Status: ${response.status}`);
      }

      if (!data) {
        throw new Error("No data returned by the server");
      }

      fidesDebugger("Successfully retrieved custom-fides.css");
      autoRefresh = true;
      cachedCustomFidesCss = data;
      lastFetched = currentTime;
    } catch (error) {
      autoRefresh = false; // /custom-asset endpoint unreachable stop auto-refresh
      if (error instanceof Error) {
        fidesError("Error during fetch operation:", error.message);
      } else {
        fidesError("Unknown error occurred:", error);
      }
    }
  }
  return cachedCustomFidesCss;
}

export const config = {
  api: {
    responseLimit: false,
  },
};
