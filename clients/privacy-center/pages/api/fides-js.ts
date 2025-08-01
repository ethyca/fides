import { CacheControl, stringify } from "cache-control-parser";
import {
  ComponentType,
  ConsentOption,
  constructFidesRegionString,
  DEFAULT_LOCALE,
  EmptyExperience,
  experienceIsValid,
  fetchExperience,
  FidesConfig,
  parseFidesDisabledNotices,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  UserGeolocation,
} from "fides-js"; // NOTE: these import from the mjs file
import { promises as fsPromises } from "fs";
import type { NextApiRequest, NextApiResponse } from "next";
import pRetry from "p-retry";

import { getFidesApiUrl, loadServerSettings } from "~/app/server-environment";
import { getPrivacyCenterEnvironmentCached } from "~/app/server-utils";
import { MissingExperienceBehaviors } from "~/app/server-utils/PrivacyCenterSettings";
import { createRequestLogger } from "~/app/server-utils/requestLogger";
import { LOCATION_HEADERS, lookupGeolocation } from "~/common/geolocation";
import { safeLookupPropertyId } from "~/common/property-id";

// one hour, how long until the custom-fides.css is refreshed
const CUSTOM_FIDES_CSS_TTL_MS = 3600 * 1000;

// a cache of the custom stylesheet retrieved from the /custom-asset endpoint
let cachedCustomFidesCss: string = "";
// millisecond timestamp of when the custom stylesheet was last retrieved
// used to determine when to refresh the contents
let lastFetched: number = 0;
// used to disable auto-refreshing if the /custom-asset endpoint is unreachable
let autoRefresh: boolean = true;

const missingExperienceBehaviors: Record<
  MissingExperienceBehaviors,
  (error: unknown) => Record<string, never>
> = {
  throw: (error) => {
    throw error;
  },
  empty_experience: () => {
    return {};
  },
};

const PREFETCH_RETRY_MIN_TIMEOUT_MS = 100;
const PREFETCH_MAX_RETRIES = 10;
const PREFETCH_BACKOFF_FACTOR = 1.125;
const CUSTOM_CSS_RETRY_MIN_TIMEOUT_MS = 100;
const CUSTOM_CSS_MAX_RETRIES = 10;
const CUSTOM_CSS_BACKOFF_FACTOR = 1.125;

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
  const log = createRequestLogger(req);
  const serverSettings = loadServerSettings();

  // Load the configured consent options (data uses, defaults, etc.) from environment
  const environment = await getPrivacyCenterEnvironmentCached({
    skipGeolocation: true,
  });

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
    log.warn(error, "Error looking up geolocation or property ID.");
    res
      .status(400) // 400 Bad Request. Malformed request.
      .send(
        error instanceof Error ? error.message : "An unknown error occurred.",
      );
    return;
  }

  if (!geolocation) {
    log.debug("No geolocation found, unable to prefetch experience.");
  } else {
    log.debug({ geolocation }, "Using geolocation");
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
  let fidesRegionString: string | undefined;
  if (
    geolocation &&
    environment.settings.IS_OVERLAY_ENABLED &&
    environment.settings.IS_PREFETCH_ENABLED &&
    !fidesString
  ) {
    fidesRegionString = constructFidesRegionString(geolocation);

    if (fidesRegionString) {
      const region = fidesRegionString;
      // Check for a provided "fides_locale" query param or cookie. If present, use it as
      // the user's preferred language, otherwise use the "accept-language" header
      // provided by the browser. If all else fails, use the default ("en").
      const fidesLocale =
        (req.query.fides_locale as string) || req.cookies?.fides_locale;
      const userLanguageString =
        fidesLocale || req.headers["accept-language"] || DEFAULT_LOCALE;

      log.info(
        {
          region,
          acceptLanguage: userLanguageString,
          propertyId,
        },
        `Fetching relevant experiences from server-side Fides API...`,
      );

      // Define how we want to handle the scenario when the API fails to gives us an experience.
      // By default the behavior is to return an empty experience, we can override that with
      // the `MISSING_EXPERIENCE_BEHAVIOR` setting. This allows us to explicitly throw an
      // error in certain cases.
      const missingExperienceHandler =
        missingExperienceBehaviors[serverSettings.MISSING_EXPERIENCE_BEHAVIOR];

      try {
        /*
         * Since we don't know what the experience will be when the initial call is made,
         * we supply the minimal request (requestMinimalTCF) to the api endpoint with the
         * understanding that if TCF is being returned, we want the minimal version. It will
         * be ignored otherwise.
         */
        experience = await pRetry(
          () =>
            fetchExperience({
              userLocationString: region,
              userLanguageString,
              fidesApiUrl: getFidesApiUrl(),
              propertyId,
              requestMinimalTCF: true,
              missingExperienceHandler,
            }),
          {
            retries: PREFETCH_MAX_RETRIES,
            factor: PREFETCH_BACKOFF_FACTOR,
            minTimeout: PREFETCH_RETRY_MIN_TIMEOUT_MS,
            onFailedAttempt: (error) => {
              log.debug(
                error,
                `Attempt to get privacy experience failed, ${error.retriesLeft} retries remain.`,
              );
            },
          },
        );
        log.debug(
          {
            experienceFound: Boolean(experience?.experience_config?.id),
            experienceConfigId: experience?.experience_config?.id,
            region: fidesRegionString,
            acceptLanguage: userLanguageString,
            propertyId,
          },
          `Fetched relevant experiences from server-side Fides API.`,
        );
        experienceIsValid(experience);
      } catch (error) {
        log.error(
          error,
          "Error fetching experience from server-side Fides API.",
        );
        throw error;
      }
    }
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
    (!!experience?.gpp_settings?.cmp_api_required ||
      forcedGppQuery === "true") &&
    forcedGppQuery !== "debug";

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
      fidesDisabledNotices: environment.settings.FIDES_DISABLED_NOTICES
        ? parseFidesDisabledNotices(environment.settings.FIDES_DISABLED_NOTICES)
        : null,
      fidesConsentNonApplicableFlagMode:
        environment.settings.FIDES_CONSENT_NON_APPLICABLE_FLAG_MODE,
      fidesConsentFlagType: environment.settings.FIDES_CONSENT_FLAG_TYPE,
      fidesInitializedEventMode:
        environment.settings.FIDES_INITIALIZED_EVENT_MODE,
    },
    experience: experience || undefined,
    geolocation: geolocation || undefined,
    propertyId: propertyId || undefined,
  };
  const fidesConfigJSON = JSON.stringify(fidesConfig);

  log.debug("Bundling js & Privacy Center configuration together...");
  const isHeadlessExperience =
    experience?.experience_config?.component === ComponentType.HEADLESS;
  let fidesJsFile = "public/lib/fides.js";
  if (tcfEnabled) {
    log.debug("TCF extension enabled, bundling fides-tcf.js...");
    fidesJsFile = "public/lib/fides-tcf.js";
  } else if (isHeadlessExperience) {
    log.debug("Headless experience detected, bundling fides-headless.js...");
    fidesJsFile = "public/lib/fides-headless.js";
  }
  const fidesJSBuffer = await fsPromises.readFile(fidesJsFile);
  const fidesJS: string = fidesJSBuffer.toString();
  if (!fidesJS || fidesJS === "") {
    throw new Error("Unable to load latest fides.js script from server!");
  }
  let fidesGPP: string = "";
  if (gppEnabled) {
    log.debug(
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

  log.info(
    {
      region: fidesRegionString,
      propertyId,
      experienceFound: Boolean(experience?.experience_config?.id),
      experienceConfigId: experience?.experience_config?.id,
      tcfEnabled,
      gppEnabled,
      isHeadlessExperience,
      customCssEnabled: Boolean(customFidesCss),
    },
    "/fides.js response complete!",
  );

  // Instruct any caches to store this response, since these bundles do not change often
  const cacheHeaders: CacheControl = {
    "max-age": serverSettings.FIDES_JS_MAX_AGE_SECONDS,
    public: true,
  };

  // Send the bundled script, ready to be loaded directly into a page!
  res
    .status(200)
    .setHeader("Content-Type", "application/javascript")
    // Allow CORS since this is a static file we do not need to lock down
    .setHeader("Access-Control-Allow-Origin", "*")
    .setHeader("Access-Control-Allow-Headers", "*")
    .setHeader("Cache-Control", stringify(cacheHeaders))
    // Ignore cache if user's geolocation or language changes
    .setHeader("Vary", [...LOCATION_HEADERS, "Accept-Language"])
    .send(script);
}

async function fetchCustomFidesCss(
  req: NextApiRequest,
): Promise<string | null> {
  const log = createRequestLogger(req);

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
      const fidesUrl = getFidesApiUrl();
      const css = await pRetry(
        async () => {
          const assetResponse = await fetch(
            `${fidesUrl}/plus/custom-asset/custom-fides.css`,
          );
          if (assetResponse.status === 404) {
            log.debug(
              "No custom-fides.css found, disabling Custom CSS polling.",
            );
            autoRefresh = false;
            return null;
          }

          const data = await assetResponse.text();
          if (!data) {
            throw new Error("No data returned by the server");
          }
          if (!assetResponse.ok) {
            log.debug(
              "Error fetching custom-fides.css:",
              assetResponse.status,
              assetResponse.statusText,
              data,
            );
            throw new Error(
              `HTTP error occurred. Status: ${assetResponse.status}`,
            );
          }

          return data;
        },
        {
          retries: CUSTOM_CSS_MAX_RETRIES,
          factor: CUSTOM_CSS_BACKOFF_FACTOR,
          minTimeout: CUSTOM_CSS_RETRY_MIN_TIMEOUT_MS,
          onFailedAttempt: (error) => {
            log.debug(
              error,
              `Attempt to get Custom CSS failed, ${error.retriesLeft} retries remain.`,
            );
          },
        },
      );

      if (!css) {
        log.debug("No custom-fides.css returned.");
        return null;
      }

      log.debug("Successfully retrieved custom-fides.css");
      autoRefresh = true;
      cachedCustomFidesCss = css;
      lastFetched = currentTime;
    } catch (error) {
      log.error(
        error,
        `Encountered an error while trying to fetch Custom CSS. Relying on cached copy.`,
      );
    }
  }
  return cachedCustomFidesCss;
}

export const config = {
  api: {
    responseLimit: false,
  },
};
