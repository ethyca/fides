import {
  ComponentType,
  ConsentMethod,
  EmptyExperience,
  FidesApiOptions,
  FidesCookie,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  PrivacyPreferencesRequest,
  RecordConsentServedRequest,
  RecordsServedResponse,
} from "../lib/consent-types";
import { Locale } from "../lib/i18n";
import sizeOf from "../lib/size-of";
import { GVLTranslations } from "../lib/tcf/types";

export enum FidesEndpointPaths {
  PRIVACY_EXPERIENCE = "/privacy-experience",
  PRIVACY_PREFERENCES = "/privacy-preferences",
  GVL_TRANSLATIONS = "/privacy-experience/gvl/translations",
  NOTICES_SERVED = "/notices-served",
}

interface FetchExperienceOptions {
  userLocationString: string;
  userLanguageString?: string;
  fidesApiUrl: string;
  apiOptions?: FidesApiOptions | null;
  propertyId: string | null | undefined;
  requestMinimalTCF?: boolean;
  missingExperienceHandler?: (error: unknown) => Record<string, never>;
}

/**
 * We allow this to be overriden in cases where falling back to an
 * empty experience is undesirable.
 */
export function createEmptyExperience() {
  return {};
}

/**
 * Fetch the relevant experience based on user location and user device id (if exists).
 * Fetches both Privacy Center and Overlay components, because GPC needs to work regardless of component
 */
export const fetchExperience = async <T = PrivacyExperience>({
  userLocationString,
  userLanguageString,
  fidesApiUrl,
  apiOptions,
  propertyId,
  requestMinimalTCF,
  missingExperienceHandler = createEmptyExperience,
}: FetchExperienceOptions): Promise<T | EmptyExperience> => {
  if (apiOptions?.getPrivacyExperienceFn) {
    fidesDebugger("Calling custom fetch experience fn");
    try {
      return await apiOptions.getPrivacyExperienceFn<T>(
        userLocationString,
        // We no longer support handling user preferences on the experience using fidesUserDeviceId.
        // For backwards compatibility, we keep fidesUserDeviceId in fn signature but pass in null here.
        null,
      );
    } catch (e) {
      fidesDebugger("Error fetching experience from custom API. Error: ", e);
      return missingExperienceHandler(e);
    }
  }

  const headers = [
    ["Unescape-Safestr", "true"],
    ["Accept-Encoding", "gzip, deflate"],
  ];
  if (userLanguageString) {
    headers.push(["Accept-Language", userLanguageString]);
  }
  const fetchOptions: RequestInit = {
    method: "GET",
    mode: "cors",
    headers: headers as HeadersInit,
  };
  let params: any = {
    show_disabled: "false",
    region: userLocationString,
    // ComponentType.OVERLAY is deprecated but “overlay” is still a backwards compatible filter.
    // Backend will filter to component that matches modal, banner_and_modal, or tcf_overlay
    component: ComponentType.OVERLAY,
    has_config: "true",
    systems_applicable: "true",
    exclude_gvl_languages: "true", // backwards compatibility for TCF optimization work
    include_meta: "true",
    include_gvl: "true",
    include_non_applicable_notices: "true",
    ...(requestMinimalTCF && { minimal_tcf: "true" }),
    ...(propertyId && { property_id: propertyId }),
  };
  params = new URLSearchParams(params);

  /* Fetch experience */
  fidesDebugger(
    `Fetching experience in location: ${userLocationString}.`,
    `${requestMinimalTCF ? "Minimal TCF requested if applicable." : ""}`,
    `${fidesApiUrl}${FidesEndpointPaths.PRIVACY_EXPERIENCE}?${params}`,
  );

  let response: Response;

  try {
    response = await fetch(
      `${fidesApiUrl}${FidesEndpointPaths.PRIVACY_EXPERIENCE}?${params}`,
      fetchOptions,
    );

    if (!response.ok) {
      throw new Error("Error fetching experience from Fides API");
    }
  } catch (error) {
    fidesDebugger("Error getting experience from Fides API. Error:", error);
    return missingExperienceHandler(error);
  }

  try {
    const body = await response.json();

    // returning empty obj instead of undefined ensures we can properly cache on
    // server-side for locations that have no relevant experiences.
    if (body.items?.length < 1) {
      return {};
    }

    const experience:
      | PrivacyExperience
      | PrivacyExperienceMinimal
      | EmptyExperience = body.items && body.items[0];

    const firstLanguage =
      experience.experience_config?.translations?.[0].language;
    fidesDebugger(
      `Received ${experience.minimal_tcf ? "minimal TCF " : ""}experience response from Fides API${experience.minimal_tcf ? ` (${firstLanguage})` : ""}`,
    );
    return experience as T;
  } catch (e) {
    fidesDebugger(
      "Error parsing experience response body from Fides API. Response:",
      response,
    );
    return missingExperienceHandler(e);
  }
};

export const fetchGvlTranslations = async (
  fidesApiUrl: string,
  locales?: Locale[],
): Promise<GVLTranslations> => {
  fidesDebugger("Calling Fides GET GVL translations API...");
  const params = new URLSearchParams();
  locales?.forEach((locale) => {
    params.append("language", locale);
  });
  const fetchOptions: RequestInit = {
    method: "GET",
    mode: "cors",
  };
  let response;
  try {
    response = await fetch(
      `${fidesApiUrl}${FidesEndpointPaths.GVL_TRANSLATIONS}${
        sizeOf(params) > 0 ? "?" : ""
      }${params.toString()}`,
      fetchOptions,
    );
  } catch (error) {
    return {};
  }
  if (!response.ok) {
    fidesDebugger("Error fetching GVL translations", response);
    return {};
  }
  const gvlTranslations: GVLTranslations = await response.json();
  fidesDebugger(
    `Received GVL languages response from Fides API (${
      Object.keys(gvlTranslations).length
    })`,
    gvlTranslations,
  );
  return gvlTranslations;
};

const PATCH_FETCH_OPTIONS: RequestInit = {
  method: "PATCH",
  mode: "cors",
  headers: {
    "Content-Type": "application/json",
  },
};

// See: PrivacyRequestSource enum in Fides
export const REQUEST_SOURCE = "Fides.js";

/**
 * Sends user consent preference downstream to Fides or custom API
 */
export const patchUserPreference = async (
  consentMethod: ConsentMethod,
  preferences: PrivacyPreferencesRequest,
  options: FidesInitOptions,
  cookie: FidesCookie,
  experience: PrivacyExperience | PrivacyExperienceMinimal,
): Promise<void> => {
  fidesDebugger("Saving user consent preference...", preferences);
  if (options.apiOptions?.savePreferencesFn) {
    fidesDebugger("Calling custom save preferences fn");
    try {
      await options.apiOptions.savePreferencesFn(
        consentMethod,
        cookie.consent,
        cookie.fides_string,
        experience,
      );
    } catch (e) {
      fidesDebugger(
        "Error saving preferences to custom API, continuing. Error: ",
        e,
      );
      return Promise.reject(e);
    }
    return Promise.resolve();
  }
  fidesDebugger("Calling Fides save preferences API");
  const fetchOptions: RequestInit = {
    ...PATCH_FETCH_OPTIONS,
    body: JSON.stringify({ ...preferences, source: REQUEST_SOURCE }),
  };
  const response = await fetch(
    `${options.fidesApiUrl}${FidesEndpointPaths.PRIVACY_PREFERENCES}`,
    fetchOptions,
  );
  if (!response.ok) {
    fidesDebugger(
      "Error patching user preference Fides API. Response:",
      response,
    );
  }
  return Promise.resolve();
};

export const patchNoticesServed = async ({
  request,
  options,
}: {
  request: RecordConsentServedRequest;
  options: FidesInitOptions;
}): Promise<RecordsServedResponse | null> => {
  fidesDebugger("Saving that notices were served...");
  if (options.apiOptions?.patchNoticesServedFn) {
    fidesDebugger("Calling custom patch notices served fn");
    try {
      return await options.apiOptions.patchNoticesServedFn(request);
    } catch (e) {
      fidesDebugger(
        "Error patching notices served to custom API, continuing. Error: ",
        e,
      );
      return null;
    }
  }
  fidesDebugger("Calling Fides patch notices served API");
  const fetchOptions: RequestInit = {
    ...PATCH_FETCH_OPTIONS,
    body: JSON.stringify(request),
  };
  try {
    const response = await fetch(
      `${options.fidesApiUrl}${FidesEndpointPaths.NOTICES_SERVED}`,
      fetchOptions,
    );
    if (!response.ok) {
      fidesDebugger("Error patching notices served. Response:", response);
      return null;
    }
    return await response.json();
  } catch (error) {
    fidesDebugger("Error patching notices served. Error:", error);
    return null;
  }
};
