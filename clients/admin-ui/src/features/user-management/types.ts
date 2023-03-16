import {
  Page_UserResponse_,
  ScopeRegistryEnum,
  UserCreate,
  UserCreateResponse,
  UserPasswordReset,
  UserPermissionsCreate,
  UserPermissionsEdit,
  UserPermissionsResponse,
  UserResponse,
  UserUpdate,
} from "~/types/api";

// Now that we have generated API types, this file can mostly re-export those interfaces.
export type {
  UserCreate,
  UserCreateResponse,
  UserPermissionsCreate,
  UserPermissionsResponse,
  UserResponse,
  UserUpdate,
};

export interface UsersResponse extends Page_UserResponse_ {}

export interface User extends UserResponse {}

export interface UserPermissions extends UserPermissionsResponse {}

export interface UserUpdateParams extends UserUpdate {
  id: string;
}

export interface UsersListParams {
  page: number;
  size: number;
  username: string;
}

export interface UserPasswordResetParams extends UserPasswordReset {
  id: string;
}

export interface UserPermissionsEditParams {
  // This is the Id of the User, not the the Id field of the UserPermissions model.
  user_id: string;
  payload: UserPermissionsEdit;
}

export interface UserPrivileges {
  privilege: string;
  scope: ScopeRegistryEnum;
}
