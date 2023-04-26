const fidesUserDeviceIdCookieKey = "fides_user_device_id";

export const setFidesUserDeviceIdCookie = () => {
  if (typeof window === "undefined") {
    return undefined;
  }
  let cookies = window.document.cookie.trim();
  const uuid = crypto.randomUUID();
  if (cookies.slice(-1) !== ';') cookies += ";";
  cookies += ` ${fidesUserDeviceIdCookieKey}=${uuid}`;
  document.cookie = cookies;
  return uuid;
}

export const getFidesUserDeviceIdCookie = () => {
  if (typeof window === "undefined") {
    return undefined;
  }
  const cookies = window.document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    const c = cookies[i].trim();
    if (c.startsWith(`${fidesUserDeviceIdCookieKey}=`)) {
      const [_, uuid] = c.split('=');
      return uuid;
    }
  }
}

export const useFidesUserDeviceIdCookie = () => {
  const cookie = getFidesUserDeviceIdCookie();
  if (!cookie) {
    return setFidesUserDeviceIdCookie();
  } else {
    return cookie;
  }
}
