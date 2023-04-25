export const setFidesUserDeviceIdCookie = () => {
  const uuid = 'something';
  // window.setCookie(uuid);
  return uuid;
}

export const useFidesUserDeviceIdCookie = () => {
  // const { cookie } = window.document;
  let cookie;
  // parse the cookie for 'fides_user_device_id'
  if (!cookie) {
    // google for how to set a cookie
    return setFidesUserDeviceIdCookie();
  } else {
    return cookie;
  }
}
