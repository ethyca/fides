/**
 * Redux-persist storage root key
 */
export const STORAGE_ROOT_KEY = "persist:root";

/**
 * Interval between re-fetching a logged-in user's permission to validate their auth token.
 * Only applies to an active page -- token will always revalidate on page refresh.
 * Ten minutes in milliseconds.
 */
export const VERIFY_AUTH_INTERVAL = 10 * 60 * 1000;

// API ROUTES
export const INDEX_ROUTE = "/";
export const LOGIN_ROUTE = "/login";
export const CONNECTION_ROUTE = "/connection";
export const PLUS_CONNECTION_API_ROUTE = "/plus/connection";
export const CONNECTION_TYPE_ROUTE = "/connection_type";
export const CONNECTOR_TEMPLATE = "/connector_template";

export const PREVIEW_CONTAINER_ID = "preview-container";
