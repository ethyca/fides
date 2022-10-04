import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "../../app/store";
import { BASE_URL } from "../../constants";
import { addCommonHeaders } from "../common/CommonHeaders";
import { utf8ToB64 } from "../common/utils";
import { User } from "../user-management/types";
import {
  LoginRequest,
  LoginResponse,
  LogoutRequest,
  LogoutResponse,
} from "./types";

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
    login(
      state,
      { payload: { user_data, token_data } }: PayloadAction<LoginResponse>
    ) {
      return Object.assign(state, {
        user: user_data,
        token: token_data.access_token,
      });
    },
    logout(state) {
      return Object.assign(state, {
        user: null,
        token: null,
      });
    },
  },
});

export const selectAuth = (state: RootState) => state.auth;
export const selectUser = (state: RootState) => selectAuth(state).user;
export const selectToken = (state: RootState) => selectAuth(state).token;

export const { login, logout } = authSlice.actions;

// Auth API
export const authApi = createApi({
  reducerPath: "authApi",
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["Auth"],
  endpoints: (build) => ({
    login: build.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: "login",
        method: "POST",
        body: { ...credentials, password: utf8ToB64(credentials.password) },
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
  }),
});

export const { useLoginMutation, useLogoutMutation } = authApi;
export const { reducer } = authSlice;
