export const setFidesDeviceUUIDCookie = () => {
  const uuid = 'something';
  // window.setCookie(uuid);
  return uuid;
}

export const useFidesDeviceUUIDCookie = () => {
  const { cookie } = window.document;
  // parse the cookie for 'fides_user_device_id'
  if (!cookie) {
    // google for how to set a cookie
    return setFidesDeviceUUIDCookie();
  } else {
    return cookie;
  }
}
