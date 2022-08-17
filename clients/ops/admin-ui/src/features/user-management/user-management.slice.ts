import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "../../app/store";
import { BASE_URL } from "../../constants";
import { selectToken } from "../auth";
import { addCommonHeaders } from "../common/CommonHeaders";
import { utf8ToB64 } from "../common/utils";
import {
  User,
  UserPasswordUpdate,
  UserPermissions,
  UserPermissionsResponse,
  UserPermissionsUpdate,
  UserResponse,
  UsersListParams,
  UsersResponse,
} from "./types";

export interface UserManagementState {
  id: string;
  page: number;
  size: number;
  username: string;
  token: string | null;
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
    assignToken: (state, action: PayloadAction<string>) => ({
      ...state,
      token: action.payload,
    }),
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
  },
});

export const { setPage, setUsernameSearch } = userManagementSlice.actions;

export const selectUserFilters = (state: RootState): UsersListParams => ({
  page: state.userManagement.page,
  size: state.userManagement.size,
  username: state.userManagement.username,
});

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

export const userApi = createApi({
  reducerPath: "userApi",
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["User"],
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
    createUser: build.mutation<UserResponse, Partial<User>>({
      query: (user) => ({
        url: "user",
        method: "POST",
        body: user,
      }),
      invalidatesTags: ["User"],
    }),
    createUserPermissions: build.mutation<
      UserPermissionsResponse,
      Partial<UserPermissionsResponse>
    >({
      query: (user) => ({
        url: `user/${user?.data?.id}/permission`,
        method: "POST",
        body: { scopes: user.scope },
      }),
      invalidatesTags: ["User"],
    }),
    editUser: build.mutation<User, Partial<User> & Pick<User, "id">>({
      query: ({ id, ...patch }) => ({
        url: `user/${id}`,
        method: "PUT",
        body: patch,
      }),
      invalidatesTags: ["User"],
      // For optimistic updates
      async onQueryStarted({ id, ...patch }, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          // @ts-ignore
          userApi.util.updateQueryData("getUserById", id, (draft) => {
            Object.assign(draft, patch);
          })
        );
        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
          /**
           * Alternatively, on failure you can invalidate the corresponding cache tags
           * to trigger a re-fetch:
           * dispatch(api.util.invalidateTags(['User']))
           */
        }
      },
    }),
    updateUserPassword: build.mutation<
      UserPasswordUpdate,
      Partial<UserPasswordUpdate> & Pick<UserPasswordUpdate, "id">
    >({
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
    updateUserPermissions: build.mutation<
      UserPermissionsUpdate,
      Partial<UserPermissionsUpdate> & Pick<UserPermissionsUpdate, "id">
    >({
      query: ({ id, scopes }) => ({
        url: `user/${id}/permission`,
        method: "PUT",
        body: { id, scopes },
      }),
      invalidatesTags: ["User"],
    }),
    deleteUser: build.mutation<{ success: boolean; id: string }, string>({
      query: (id) => ({
        url: `user/${id}`,
        method: "DELETE",
      }),
      // Invalidates all queries that subscribe to this User `id` only
      invalidatesTags: ["User"],
    }),
  }),
});

export const {
  useGetAllUsersQuery,
  useGetUserByIdQuery,
  useCreateUserMutation,
  useEditUserMutation,
  useDeleteUserMutation,
  useUpdateUserPasswordMutation,
  useUpdateUserPermissionsMutation,
  useCreateUserPermissionsMutation,
  useGetUserPermissionsQuery,
} = userApi;
