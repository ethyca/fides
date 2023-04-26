import { getCookie, setCookie, Types } from "typescript-cookie";

const FIDES_USER_DEVICE_ID_COOKIE_NAME = "fides_user_device_id";
const MAX_AGE_DAYS = 1;

const CODEC: Types.CookieCodecConfig<string, string> = {
  decodeName: decodeURIComponent,
  decodeValue: decodeURIComponent,
  encodeName: encodeURIComponent,
  encodeValue: encodeURIComponent,
};

export const setFidesUserDeviceIdCookie = () => {
  // Generates a new `fides_user_device_id` and stores it to the cookie
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
}

export const getFidesUserDeviceIdCookie = () => {
  // Returns the `fides_user_device_id` from the cookie
  if (typeof document === "undefined") {
    return undefined;
  }

  return getCookie(FIDES_USER_DEVICE_ID_COOKIE_NAME, CODEC);
}

export const useFidesUserDeviceIdCookie = () => {
  const cookie = getFidesUserDeviceIdCookie();
  if (!cookie) {
    return setFidesUserDeviceIdCookie();
  }
  return cookie;
}
