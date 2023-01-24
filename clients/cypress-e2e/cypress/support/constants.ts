/**
 * Based off of fides.toml
 *
 * TODO: if this becomes too cumbersome to keep in sync, we may also want to look
 * into other ways of sharing constants
 * https://docs.cypress.io/guides/guides/environment-variables#Option-3-CYPRESS_
 */
export const CREDENTIALS = {
  username: "root_user",
  password: "Testpassword1!",
};

export const API_URL = "http://0.0.0.0:8080/api/v1";
export const ADMIN_UI_URL = "http://localhost:3000";
export const PRIVACY_CENTER_URL = "http://localhost:3001";
