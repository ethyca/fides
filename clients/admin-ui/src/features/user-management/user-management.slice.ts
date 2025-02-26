import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { utf8ToB64 } from "common/utils";

import type { RootState } from "~/app/store";
import { selectUser } from "~/features/auth";
import { baseApi } from "~/features/common/api.slice";
import {
  RoleRegistryEnum,
  ScopeRegistryEnum,
  System,
  UserForcePasswordReset,
} from "~/types/api";

import {
  User,
  UserCreate,
  UserCreateResponse,
  UserPasswordResetParams,
  UserPermissions,
  UserPermissionsEditParams,
  UserResponse,
  UsersListParams,
  UsersResponse,
  UserUpdateParams,
} from "./types";

export interface UserManagementState {
  id: string;
  page: number;
  size: number;
  username: string;
  token: string | null;
  activeUserId?: User["id"];
}

const initialState: UserManagementState = {
  id: "",
  page: 1,
  size: 25,
  token: null,
  username: "",
};

export const userManagementSlice = createSlice({
  name: "userManagement",
  initialState,
  reducers: {
    setUsernameSearch: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      username: action.payload,
    }),
    setPage: (state, action: PayloadAction<number>) => ({
      ...state,
      page: action.payload,
    }),
    setSize: (state, action: PayloadAction<number>) => ({
      ...state,
      page: initialState.page,
      size: action.payload,
    }),
    setActiveUserId: (
      state,
      action: PayloadAction<User["id"] | undefined>,
    ) => ({
      ...state,
      activeUserId: action.payload,
    }),
  },
});

export const { setPage, setUsernameSearch, setActiveUserId } =
  userManagementSlice.actions;

export const { reducer } = userManagementSlice;

// Helpers
export const mapFiltersToSearchParams = ({
  page,
  size,
  username,
}: Partial<UsersListParams>) => ({
  ...(page ? { page: `${page}` } : {}),
  ...(typeof size !== "undefined" ? { size: `${size}` } : {}),
  ...(username ? { username } : {}),
});

const userApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllUsers: build.query<UsersResponse, UsersListParams>({
      query: (filters) => ({
        url: `user`,
        params: mapFiltersToSearchParams(filters),
      }),
      providesTags: () => ["User"],
    }),
    getUserById: build.query<User, string>({
      query: (id) => ({ url: `user/${id}` }),
      providesTags: ["User"],
    }),
    getUserPermissions: build.query<UserPermissions, string>({
      query: (id) => ({ url: `user/${id}/permission` }),
      providesTags: ["User"],
    }),
    createUser: build.mutation<UserCreateResponse, UserCreate>({
      query: (user) => ({
        url: "user",
        method: "POST",
        body: user,
      }),
      invalidatesTags: ["User"],
    }),
    editUser: build.mutation<User, UserUpdateParams>({
      query: ({ id, ...patch }) => ({
        url: `user/${id}`,
        method: "PUT",
        body: patch,
      }),
      invalidatesTags: ["User"],
    }),
    updateUserPassword: build.mutation<UserResponse, UserPasswordResetParams>({
      query: ({ id, old_password, new_password }) => ({
        url: `user/${id}/reset-password`,
        method: "POST",
        body: {
          old_password: utf8ToB64(old_password!),
          new_password: utf8ToB64(new_password!),
        },
      }),
      invalidatesTags: ["User"],
    }),
    forceResetUserPassword: build.mutation<
      UserResponse,
      { id: string } & UserForcePasswordReset
    >({
      query: ({ id, new_password }) => ({
        url: `user/${id}/force-reset-password`,
        method: "POST",
        body: {
          new_password: utf8ToB64(new_password),
        },
      }),
      invalidatesTags: ["User"],
    }),
    updateUserPermissions: build.mutation<
      UserPermissions,
      UserPermissionsEditParams
    >({
      query: ({ user_id, payload }) => ({
        url: `user/${user_id}/permission`,
        method: "PUT",
        body: payload,
      }),
      invalidatesTags: (result, error, arg) => {
        // The backend will change managed systems if the role becomes "Approver"
        // so make sure we refetch for the managed systems in this case
        if (arg.payload.roles?.includes(RoleRegistryEnum.APPROVER)) {
          return [
            "User",
            { type: "Managed Systems" as const, id: arg.user_id },
          ];
        }
        return ["User"];
      },
    }),
    deleteUser: build.mutation<{ success: boolean; id: string }, string>({
      query: (id) => ({
        url: `user/${id}`,
        method: "DELETE",
      }),
      // Invalidates all queries that subscribe to this User `id` only
      invalidatesTags: ["User"],
    }),

    // Data steward endpoints
    getUserManagedSystems: build.query<System[], string>({
      query: (id) => ({ url: `user/${id}/system-manager` }),
      providesTags: (result, error, arg) => [
        { type: "Managed Systems" as const, id: arg },
      ],
    }),
    updateUserManagedSystems: build.mutation<
      System[],
      { fidesKeys: string[]; userId: string }
    >({
      query: ({ userId, fidesKeys }) => ({
        url: `user/${userId}/system-manager`,
        method: "PUT",
        body: fidesKeys,
      }),
      invalidatesTags: (result, error, arg) => [
        { type: "Managed Systems" as const, id: arg.userId },
      ],
    }),
    removeUserManagedSystem: build.mutation<
      void,
      { userId: string; systemKey: string }
    >({
      query: ({ userId, systemKey }) => ({
        url: `user/${userId}/system-manager/${systemKey}`,
        method: "DELETE",
      }),
      invalidatesTags: (result, error, arg) => [
        { type: "Managed Systems" as const, id: arg.userId },
      ],
    }),
  }),
});

export const selectUserFilters = (state: RootState): UsersListParams => ({
  page: state.userManagement.page,
  size: state.userManagement.size,
  username: state.userManagement.username,
});

const selectUserManagement = (state: RootState) => state.userManagement;

export const selectActiveUserId = createSelector(
  selectUserManagement,
  (state) => state.activeUserId,
);

export const selectActiveUser = createSelector(
  [(RootState) => RootState, selectActiveUserId],
  (RootState, userId) => {
    if (!userId) {
      return undefined;
    }
    return userApi.endpoints.getUserById.select(userId)(RootState).data;
  },
);

const emptyScopes: ScopeRegistryEnum[] = [];
export const selectThisUsersScopes: (state: RootState) => ScopeRegistryEnum[] =
  createSelector([(RootState) => RootState, selectUser], (RootState, user) => {
    if (!user) {
      return emptyScopes;
    }
    const permissions = userApi.endpoints.getUserPermissions.select(user.id)(
      RootState,
    ).data;

    return permissions ? permissions.total_scopes : emptyScopes;
  });

const emptyRoles: RoleRegistryEnum[] = [];
/**
 * In general, the UI should restrict based off of scopes, not roles to allow
 * for flexibility when adding or removing roles.
 * There are however, some unique cases where it is more useful to restrict
 * off of role than scope. Make sure you use this selector intentionally!
 */
export const selectThisUsersRoles = createSelector(
  [(RootState) => RootState, selectUser],
  (RootState, user) => {
    if (!user) {
      return emptyRoles;
    }
    const permissions = userApi.endpoints.getUserPermissions.select(user.id)(
      RootState,
    ).data;

    return permissions?.roles ?? emptyRoles;
  },
);

const emptyManagedSystems: System[] = [];
export const selectActiveUsersManagedSystems = createSelector(
  [(RootState) => RootState, selectActiveUserId],
  (RootState, activeUserId) => {
    if (!activeUserId) {
      return emptyManagedSystems;
    }
    const systems =
      userApi.endpoints.getUserManagedSystems.select(activeUserId)(
        RootState,
      ).data;
    return systems ?? emptyManagedSystems;
  },
);

export const {
  useGetAllUsersQuery,
  useGetUserByIdQuery,
  useCreateUserMutation,
  useEditUserMutation,
  useDeleteUserMutation,
  useUpdateUserPasswordMutation,
  useUpdateUserPermissionsMutation,
  useGetUserPermissionsQuery,
  useForceResetUserPasswordMutation,

  useGetUserManagedSystemsQuery,
  useUpdateUserManagedSystemsMutation,
  useRemoveUserManagedSystemMutation,
} = userApi;
