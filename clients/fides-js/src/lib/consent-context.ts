import {
  readConsentFromAnyProvider,
  registerDefaultProviders,
} from "./consent-migration";
import {
  ConsentMethod,
  FidesInitOptions,
  FidesInitOptionsOverrides,
  NoticeConsent,
} from "./consent-types";
import { hasFidesConsentCookie } from "./cookie";
import { decodeFidesString } from "./fides-string";

declare global {
  interface Navigator {
    globalPrivacyControl?: boolean;
  }
}

/**
 * Returns `window.navigator.globalPrivacyControl` as defined by the spec.
 *
 * If the GPC value is not true, then current page URL is checked for a `globalPrivacyControl`
 * query parameter. For example: `privacy-center.example.com/consent?globalPrivacyControl=true`.
 * This allows fides.js to function as if GPC is enabled while testing or demoing without
 * having to modify the browser before the script runs.
 */
const getGlobalPrivacyControl = (): boolean | undefined => {
  if (window.navigator?.globalPrivacyControl === true) {
    // NOTE: When GPC is disabled Firefox returns `false`, other browsers return `undefined`.
    return window.navigator.globalPrivacyControl;
  }

  const url = new URL(window.location.href);
  const gpcParam = url.searchParams.get("globalPrivacyControl");
  if (gpcParam === "true") {
    return true;
  }
  if (gpcParam === "false") {
    return false;
  }

  // will be undefined or false depending on the browser
  return window.navigator?.globalPrivacyControl;
};

export interface AutomatedConsentContext {
  globalPrivacyControl?: boolean;
  migratedConsent?: NoticeConsent;
  migrationMethod?: ConsentMethod;
  noticeConsentString?: string;
  hasFidesCookie?: boolean;
}

/**
 * Returns the GPC context from the browser/document.
 * This function specifically returns GPC status only.
 */
export const getGpcStatus = (): { globalPrivacyControl?: boolean } => {
  if (typeof window === "undefined") {
    return {};
  }

  return {
    globalPrivacyControl: getGlobalPrivacyControl(),
  };
};

/**
 * Returns the complete automated consent context by reading all automated consent sources.
 * This includes GPC, migrated consent from third-party providers (like OneTrust),
 * and notice consent string overrides from options.
 *
 * This function is synchronous and should be called early in initialization before the experience API call.
 *
 * @param options - Fides initialization options
 * @param optionsOverrides - Overrides containing provider mappings and other configuration
 * @returns Complete ConsentContext with all automated consent sources
 */
export const getAutomatedConsentContext = (
  options: FidesInitOptions,
  optionsOverrides: Partial<FidesInitOptionsOverrides>,
): AutomatedConsentContext => {
  const context: AutomatedConsentContext = {};

  // Check if a Fides cookie already exists
  context.hasFidesCookie = hasFidesConsentCookie(options.fidesCookieSuffix);

  // Read GPC status
  context.globalPrivacyControl = getGlobalPrivacyControl();

  // Register and read migrated consent from third-party providers (e.g., OneTrust)
  registerDefaultProviders(optionsOverrides);
  const { consent: migratedConsent, method: migrationMethod } =
    readConsentFromAnyProvider(optionsOverrides);

  if (migratedConsent && migrationMethod) {
    context.migratedConsent = migratedConsent;
    context.migrationMethod = migrationMethod;
  }

  // Extract notice consent string from fidesString option
  const { nc: noticeConsentString } = decodeFidesString(
    options.fidesString ?? "",
  );

  if (noticeConsentString) {
    context.noticeConsentString = noticeConsentString;
  }

  return context;
};
