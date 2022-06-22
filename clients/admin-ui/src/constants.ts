import { UserPrivileges } from "./features/user-management/types";

export const BASE_API_URN = "/api/v1";
export const BASE_ASSET_URN =
  process.env.NODE_ENV === "development" ? "" : "/static";
const API_URL = process.env.NEXT_PUBLIC_FIDESOPS_API
  ? process.env.NEXT_PUBLIC_FIDESOPS_API
  : "";
export const BASE_URL = API_URL + BASE_API_URN;

export const STORED_CREDENTIALS_KEY = "auth.fidesops-admin-ui";

export const USER_PRIVILEGES: UserPrivileges[] = [
  {
    privilege: "View subject requests",
    scope: "privacy-request:read",
  },
  {
    privilege: "Approve subject requests",
    scope: "privacy-request:review",
  },
  {
    privilege: "View datastore connections",
    scope: "connection:read",
  },
  {
    privilege: "Create or Update datastore connections",
    scope: "connection:create_or_update",
  },
  {
    privilege: "Delete datastore connections",
    scope: "connection:delete",
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
    privilege: "Create roles",
    scope: "user-permission:create",
  },
  {
    privilege: "View roles",
    scope: "user-permission:read",
  },
];

// API ROUTES
export const INDEX_ROUTE = "/";
export const LOGIN_ROUTE = "/login";
export const USER_MANAGEMENT_ROUTE = "/user-management";
export const CONNECTION_ROUTE = "/connection";

// UI ROUTES
export const DATASTORE_CONNECTION_ROUTE = "/datastore-connection";
