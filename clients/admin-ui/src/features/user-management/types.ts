import {
  Page_UserResponse_,
  ScopeRegistryEnum,
  UserCreateExtended,
  UserCreateResponse,
  UserPasswordReset,
  UserPermissionsCreate,
  UserPermissionsEdit,
  UserPermissionsPlusResponse,
  UserResponse,
  UserResponseExtended,
  UserUpdate,
} from "~/types/api";

// Now that we have generated API types, this file can mostly re-export those interfaces.
export type {
  UserCreateExtended,
  UserCreateResponse,
  UserPermissionsCreate,
  UserPermissionsPlusResponse,
  UserResponse,
  UserResponseExtended,
  UserUpdate,
};

export interface UsersResponse extends Page_UserResponse_ {}

export interface User extends UserResponseExtended {}

export interface UserPermissions extends UserPermissionsPlusResponse {}

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
