export interface User {
  id?: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  password?: string;
  created_at?: string;
}

export interface UserResponse {
  id: string;
}

export interface UsersResponse {
  items: User[];
  total: number;
}

export interface UsersListParams {
  page: number;
  size: number;
  user: User;
}

export interface UserPasswordUpdate {
  id: string | null;
  old_password: string;
  new_password: string;
}

export interface UserPermissionsUpdate {
  id: string | null;
  scopes: never[];
}

export interface UserPermissionsResponse {
  data: {
    id: string;
  };
  scope: string[];
}

export interface UserPrivileges {
  privilege: string;
  scope: string;
}

export const userPrivilegesArray: UserPrivileges[] = [
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
