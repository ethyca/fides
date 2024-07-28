import { UserPrivileges } from "user-management/types";

import { ScopeRegistryEnum } from "./types/api";

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
    scope: ScopeRegistryEnum.PRIVACY_REQUEST_READ,
  },
  {
    privilege: "Approve privacy requests",
    scope: ScopeRegistryEnum.PRIVACY_REQUEST_REVIEW,
  },
  {
    privilege: "Resume privacy requests",
    scope: ScopeRegistryEnum.PRIVACY_REQUEST_RESUME,
  },
  {
    privilege: "View connections",
    scope: ScopeRegistryEnum.CONNECTION_READ,
  },
  {
    privilege: "Create or update connections",
    scope: ScopeRegistryEnum.CONNECTION_CREATE_OR_UPDATE,
  },
  {
    privilege: "Instantiate connections",
    scope: ScopeRegistryEnum.CONNECTION_INSTANTIATE,
  },
  {
    privilege: "Read connection types",
    scope: ScopeRegistryEnum.CONNECTION_TYPE_READ,
  },
  {
    privilege: "Delete connections",
    scope: ScopeRegistryEnum.CONNECTION_DELETE,
  },
  {
    privilege: "View user consent preferences",
    scope: ScopeRegistryEnum.CONSENT_READ,
  },
  {
    privilege: "View datasets",
    scope: ScopeRegistryEnum.DATASET_READ,
  },
  {
    privilege: "Create or update datasets",
    scope: ScopeRegistryEnum.DATASET_CREATE_OR_UPDATE,
  },
  {
    privilege: "Delete datasets",
    scope: ScopeRegistryEnum.DATASET_DELETE,
  },
  {
    privilege: "View policies",
    scope: ScopeRegistryEnum.POLICY_READ,
  },
  {
    privilege: "Create policies",
    scope: ScopeRegistryEnum.POLICY_CREATE_OR_UPDATE,
  },
  {
    privilege: "View users",
    scope: ScopeRegistryEnum.USER_READ,
  },
  {
    privilege: "Create users",
    scope: ScopeRegistryEnum.USER_CREATE,
  },
  {
    privilege: "Update users",
    scope: ScopeRegistryEnum.USER_UPDATE,
  },
  {
    privilege: "Delete users",
    scope: ScopeRegistryEnum.USER_DELETE,
  },
  {
    privilege: "Reset another user's password",
    scope: ScopeRegistryEnum.USER_PASSWORD_RESET,
  },
  {
    privilege: "Assign user permissions",
    scope: ScopeRegistryEnum.USER_PERMISSION_CREATE,
  },
  {
    privilege: "Update user permissions",
    scope: ScopeRegistryEnum.USER_PERMISSION_UPDATE,
  },
  {
    privilege: "Read user permissions",
    scope: ScopeRegistryEnum.USER_PERMISSION_READ,
  },
  {
    privilege: "Upload privacy request data",
    scope: ScopeRegistryEnum.PRIVACY_REQUEST_UPLOAD_DATA,
  },
  {
    privilege: "View privacy request data",
    scope: ScopeRegistryEnum.PRIVACY_REQUEST_VIEW_DATA,
  },
  {
    privilege: "Create manual processes",
    scope: ScopeRegistryEnum.WEBHOOK_CREATE_OR_UPDATE,
  },
  {
    privilege: "Read manual processes",
    scope: ScopeRegistryEnum.WEBHOOK_READ,
  },
  {
    privilege: "Delete manual processes",
    scope: ScopeRegistryEnum.WEBHOOK_DELETE,
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
export const CONNECTION_ROUTE = "/connection";
export const CONNECTION_TYPE_ROUTE = "/connection_type";
export const CONNECTOR_TEMPLATE = "/connector_template";

export const PREVIEW_CONTAINER_ID = "preview-container";
