interface BrowserIdentities {
  gaClientId?: string;
}

/**
 * With some consent requests, we also want to send information that only
 * the browser would know about, for example, the value of a Google Analytics
 * cookie.
 *
 * Inspects the cookies on this site and returns a relevant user ID.
 *
 * Currently hard coded to Google Analytics until we have evidence of other
 * identities we may want to leverage.
 */
const GA_COOKIE_KEY = "_ga";
// The GA cookie only uses the last two sections as the clientId
const GA_COOKIE_REGEX = /=\w+\.\w+\.(\w+\.\w+)/;

export const inspectForBrowserIdentities = ():
  | BrowserIdentities
  | undefined => {
  if (typeof window === "undefined") {
    return undefined;
  }

  // Returns a string of all cookies on the page separated by semicolons
  // For example, 'cookie1=value1; cookie2=value2'
  const { cookie } = window.document;

  const gaCookie = cookie
    .split("; ")
    .filter((c) => c.startsWith(`${GA_COOKIE_KEY}=`))[0];
  if (!gaCookie) {
    return undefined;
  }
  const match = gaCookie.match(GA_COOKIE_REGEX);
  const gaClientId = match ? match[1] : undefined;
  return { gaClientId };
};
