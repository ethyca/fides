declare global {
  interface Navigator {
    globalPrivacyControl?: boolean;
  }
}

/**
 * Returns `window.navigator.globalPrivacyControl` as defined by the spec.
 *
 * If the GPC value is undefined, then current page URL is checked for a `globalPrivacyControl`
 * query parameter. For example: `privacy-center.example.com/consent?globalPrivacyControl=true`.
 * This allows fides.js to function as if GPC is enabled while testing or demoing without
 * having to modify the browser before the script runs.
 *
 * GPC is not considered for standard TCF purposes/vendors when TCF is enabled, but it can
 * still be applied to custom privacy notices in TCF experiences.
 */
const getGlobalPrivacyControl = (): boolean | undefined => {
  if (
    window.Fides.options.tcfEnabled &&
    !window.Fides.experience?.privacy_notices?.length
  ) {
    return false;
  }

  if (typeof window.navigator?.globalPrivacyControl === "boolean") {
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

  return undefined;
};

export type ConsentContext = {
  globalPrivacyControl?: boolean;
};

/**
 * Returns the context in which consent should be evaluated. This includes information from the
 * browser/document, such as whether GPC is enabled.
 */
export const getConsentContext = (): ConsentContext => {
  if (typeof window === "undefined") {
    return {};
  }

  return {
    globalPrivacyControl: getGlobalPrivacyControl(),
  };
};
