import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { utf8ToB64 } from "~/features/common/utils";
import { User } from "~/features/user-management/types";
import { RoleRegistryEnum, ScopeRegistryEnum } from "~/types/api";

import {
  AuthenticationMethods,
  LoginRequest,
  LoginResponse,
  LoginWithOIDCRequest,
  LogoutRequest,
  LogoutResponse,
} from "./types";

// Currently, the BE response doesn't include whether the user is a root user,
// so we need to check if the id matches a db user id.
export const isRootUserId = (userId?: string): boolean => {
  if (!userId) {
    return false;
  }
  return !userId.toLowerCase().startsWith("fid_");
};

export interface AuthState {
  user: User | null;
  token: string | null;
}

const initialState: AuthState = {
  token: null,
  user: null,
};

// Auth slice
export const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    login(draftState, action: PayloadAction<LoginResponse>) {
      draftState.user = action.payload.user_data;
      draftState.token = action.payload.token_data.access_token;
    },
    logout(draftState) {
      draftState.user = null;
      draftState.token = null;
    },
  },
});

export const selectAuth = (state: RootState) => state.auth;

// Enhanced user selector that includes isRootUser property
export const selectUser = (state: RootState) => {
  const { user } = selectAuth(state);
  if (!user) {
    return null;
  }

  // Currently, the BE response doesn't include whether the user is a root user,
  // so we need to check if the id matches a db user id.
  const isRootUser = isRootUserId(user.id);

  return {
    ...user,
    isRootUser,
  };
};

export const selectToken = (state: RootState) => selectAuth(state).token;

export const { login, logout } = authSlice.actions;

type RoleToScopes = Record<RoleRegistryEnum, ScopeRegistryEnum[]>;

// Auth API
const authApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    login: build.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: "login",
        method: "POST",
        body: { ...credentials, password: utf8ToB64(credentials.password) },
      }),
      invalidatesTags: () => ["Auth"],
    }),
    loginWithOIDC: build.mutation<LoginResponse, LoginWithOIDCRequest>({
      query: (data) => ({
        url: `plus/openid-provider/${data.provider}/callback?code=${data.code}`,
        method: "GET",
      }),
      invalidatesTags: () => ["Auth"],
    }),
    logout: build.mutation<LogoutResponse, LogoutRequest>({
      query: () => ({
        url: "logout",
        method: "POST",
      }),
      invalidatesTags: () => ["Auth"],
    }),
    getRolesToScopesMapping: build.query<RoleToScopes, void>({
      query: () => ({ url: `oauth/role` }),
      providesTags: ["Roles"],
    }),
    acceptInvite: build.mutation<
      LoginResponse,
      LoginRequest & { inviteCode: string }
    >({
      query: ({ username, password, inviteCode }) => ({
        url: "/user/accept-invite",
        params: { username, invite_code: inviteCode },
        method: "POST",
        body: { new_password: password },
      }),
    }),
    getAuthenticationMethods: build.query<AuthenticationMethods, void>({
      query: () => ({
        url: "plus/authentication-methods",
        method: "GET",
      }),
    }),
  }),
});

export const {
  useLoginMutation,
  useLoginWithOIDCMutation,
  useLogoutMutation,
  useAcceptInviteMutation,
  useGetRolesToScopesMappingQuery,
  useGetAuthenticationMethodsQuery,
} = authApi;
export const { reducer } = authSlice;
