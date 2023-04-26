import { getCookie, setCookie, Types } from "typescript-cookie";

const FIDES_USER_DEVICE_ID_COOKIE_NAME = "fides_user_device_id";
const MAX_AGE_DAYS = 1;

const CODEC: Types.CookieCodecConfig<string, string> = {
  decodeName: decodeURIComponent,
  decodeValue: decodeURIComponent,
  encodeName: encodeURIComponent,
  encodeValue: encodeURIComponent,
};
/**
 * Generates a new `fides_user_device_id` and stores it to the cookie
 */
const setFidesUserDeviceIdCookie = () => {
  if (typeof document === "undefined") {
    return undefined;
  }

  const rootDomain = window.location.hostname.split(".").slice(-2).join(".");
  const uuid = crypto.randomUUID();

  setCookie(
    FIDES_USER_DEVICE_ID_COOKIE_NAME,
    uuid,
    {
      domain: rootDomain,
      expires: MAX_AGE_DAYS,
    },
    CODEC
  );
  return uuid;
};

/**
 * Returns the `fides_user_device_id` from the cookie
 */
const getFidesUserDeviceIdCookie = () => {
  if (typeof document === "undefined") {
    return undefined;
  }

  return getCookie(FIDES_USER_DEVICE_ID_COOKIE_NAME, CODEC);
};

/**
 * Retrieves the fides user device UUID as stored in the `fides_user_device_id` cookie
 * If no cookie is found, sets a new UUID on the cookie and returns the value
 */
export const getFidesUserDeviceUuid = () => {
  const cookie = getFidesUserDeviceIdCookie();
  if (!cookie) {
    return setFidesUserDeviceIdCookie();
  }
  return cookie;
};
