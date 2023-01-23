import { UserPrivileges } from "user-management/types";

export const BASE_API_URN = "/api/v1";
const API_URL = process.env.NEXT_PUBLIC_FIDESOPS_API
  ? process.env.NEXT_PUBLIC_FIDESOPS_API
  : "";
export const BASE_URL = API_URL + BASE_API_URN;

/**
 * Redux-persist storage root key
 */
export const STORAGE_ROOT_KEY = "persist:root";

export const USER_PRIVILEGES: UserPrivileges[] = [
  {
    privilege: "View privacy requests",
    scope: "privacy-request:read",
  },
  {
    privilege: "Approve privacy requests",
    scope: "privacy-request:review",
  },
  {
    privilege: "Resume privacy requests",
    scope: "privacy-request:resume",
  },
  {
    privilege: "View connections",
    scope: "connection:read",
  },
  {
    privilege: "Create or update connections",
    scope: "connection:create_or_update",
  },
  {
    privilege: "Instantiate connections",
    scope: "connection:instantiate",
  },
  {
    privilege: "Read connection types",
    scope: "connection_type:read",
  },
  {
    privilege: "Delete connections",
    scope: "connection:delete",
  },
  {
    privilege: "View user consent preferences",
    scope: "consent:read",
  },
  {
    privilege: "View datasets",
    scope: "dataset:read",
  },
  {
    privilege: "Create or update datasets",
    scope: "dataset:create_or_update",
  },
  {
    privilege: "Delete datasets",
    scope: "dataset:delete",
  },
  {
    privilege: "View policies",
    scope: "policy:read",
  },
  {
    privilege: "Create policies",
    scope: "policy:create_or_update",
  },
  {
    privilege: "View users",
    scope: "user:read",
  },
  {
    privilege: "Create users",
    scope: "user:create",
  },
  {
    privilege: "Update users",
    scope: "user:update",
  },
  {
    privilege: "Delete users",
    scope: "user:delete",
  },
  {
    privilege: "Reset their own password",
    scope: "user:reset-password",
  },
  {
    privilege: "Assign user permissions",
    scope: "user-permission:create",
  },
  {
    privilege: "Update user permissions",
    scope: "user-permission:update",
  },
  {
    privilege: "Read user permissions",
    scope: "user-permission:read",
  },
  {
    privilege: "Upload privacy request data",
    scope: "privacy-request:upload_data",
  },
  {
    privilege: "View privacy request data",
    scope: "privacy-request:view_data",
  },
  {
    privilege: "Create manual webhooks",
    scope: "webhook:create_or_update",
  },
  {
    privilege: "Read manual webhooks",
    scope: "webhook:read",
  },
  {
    privilege: "Delete manual webhooks",
    scope: "webhook:delete",
  },
];

/**
 * Interval between re-fetching a logged-in user's permission to validate their auth token.
 * Only applies to an active page -- token will always revalidate on page refresh.
 * Ten minutes in milliseconds.
 */
export const VERIFY_AUTH_INTERVAL = 10 * 60 * 1000;

// API ROUTES
export const INDEX_ROUTE = "/";
export const LOGIN_ROUTE = "/login";
export const USER_MANAGEMENT_ROUTE = "/user-management";
export const CONNECTION_ROUTE = "/connection";
export const CONNECTION_TYPE_ROUTE = "/connection_type";

// UI ROUTES
export const CONFIG_WIZARD_ROUTE = "/add-systems";
export const DATAMAP_ROUTE = "/datamap";
export const DATASTORE_CONNECTION_ROUTE = "/datastore-connection";
export const PRIVACY_REQUESTS_ROUTE = "/privacy-requests";
export const SYSTEM_ROUTE = "/system";
