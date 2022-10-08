import { getCookie, setCookie } from "typescript-cookie";

import config from "~/config/config.json";

import { DataUseConsent } from "./types";

export const CONSENT_COOKIE_NAME =
  config.consent?.cookieName ?? "ethyca_consent";

export const CONSENT_COOKIE_MAX_AGE_DAYS = 365;

export const getConsentCookie = (): DataUseConsent => {
  if (typeof document === "undefined") {
    return {};
  }

  const cookie = getCookie(CONSENT_COOKIE_NAME);
  if (!cookie) {
    return {};
  }

  try {
    return JSON.parse(cookie);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error("Unable to read consent cookie: invalid JSON.", err);
    return {};
  }
};

export const setConsentCookie = (dataUseConsent: DataUseConsent) => {
  if (typeof document === "undefined") {
    return;
  }

  setCookie(CONSENT_COOKIE_NAME, JSON.stringify(dataUseConsent), {
    // An explicit domain allows subdomains to access the cookie.
    domain: window.location.hostname,
    expires: CONSENT_COOKIE_MAX_AGE_DAYS,
  });
};
