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
  username: string;
}

export interface UserPasswordUpdate {
  id: string;
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

export type CreateUserError = {
  detail: {
    msg: string;
  }[];
};
