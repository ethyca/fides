interface BrowserIdentities {
  ga_client_id?: string;
  ljt_readerID?: string;
}

interface CookieConfig {
  key: keyof BrowserIdentities;
  cookieKey: string;
  regex?: RegExp;
}

const DEFAULT_REGEX = /=(\w+)/;

const GA_COOKIE_KEY = "_ga";
// The GA cookie only uses the last two sections as the clientId
const GA_COOKIE_REGEX = /=\w+\.\w+\.(\w+\.\w+)/;

const SOVRN_COOKIE_KEY = "ljt_readerID";

const COOKIES: CookieConfig[] = [
  { key: "ga_client_id", cookieKey: GA_COOKIE_KEY, regex: GA_COOKIE_REGEX },
  { key: SOVRN_COOKIE_KEY, cookieKey: SOVRN_COOKIE_KEY },
];

/**
 * With some consent requests, we also want to send information that only
 * the browser would know about, for example, the value of a Google Analytics
 * cookie.
 *
 * Inspects the cookies on this site and returns a relevant user ID.
 *
 * Currently hard coded to Google Analytics + Sovrn until we have evidence of other
 * identities we may want to leverage.
 */
export const inspectForBrowserIdentities = ():
  | BrowserIdentities
  | undefined => {
  if (typeof window === "undefined") {
    return undefined;
  }

  // Returns a string of all cookies on the page separated by semicolons
  // For example, 'cookie1=value1; cookie2=value2'
  const { cookie } = window.document;

  const browserIdentities: BrowserIdentities = {};

  COOKIES.forEach((cookieConfig) => {
    const thisCookie = cookie
      .split("; ")
      .filter((c) => c.startsWith(`${cookieConfig.cookieKey}=`))[0];

    if (thisCookie) {
      // if (cookieConfig.regex) {
      const match = thisCookie.match(cookieConfig.regex ?? DEFAULT_REGEX);
      browserIdentities[cookieConfig.key] = match ? match[1] : undefined;
      // } else {
      //   // eslint-disable-next-line prefer-destructuring
      //   browserIdentities[cookieConfig.key] = thisCookie.split(
      //     `${cookieConfig.cookieKey}=`
      //   )[1];
      // }
    }
  });
  console.log({ browserIdentities });

  return Object.keys(browserIdentities).length > 0
    ? browserIdentities
    : undefined;
};
