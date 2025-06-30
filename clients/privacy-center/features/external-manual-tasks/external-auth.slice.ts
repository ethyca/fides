/**
 * External Authentication Slice
 *
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/auth/auth.slice.ts
 *
 * Key differences for external users:
 * - Two-step authentication (request OTP + verify OTP)
 * - Uses real plus/external-login endpoints (no mocking)
 * - Simplified state management (no complex role/permission handling)
 * - Always filtered to current external user
 *
 * IMPORTANT: When updating admin-ui auth.slice.ts, review this slice for sync!
 */

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";

import {
  ExternalUser,
  OtpRequestPayload,
  OtpRequestResponse,
  OtpVerifyPayload,
  OtpVerifyResponse,
} from "./types";

// External Auth State
export interface ExternalAuthState {
  isAuthenticated: boolean;
  token: string | null;
  user: ExternalUser | null;
  emailToken: string | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: ExternalAuthState = {
  isAuthenticated: false,
  token: null,
  user: null,
  emailToken: null,
  isLoading: false,
  error: null,
};

// External Auth Slice
export const externalAuthSlice = createSlice({
  name: "externalAuth",
  initialState,
  reducers: {
    setEmailToken(draftState, action: PayloadAction<string>) {
      draftState.emailToken = action.payload;
      draftState.error = null;
    },
    setLoading(draftState, action: PayloadAction<boolean>) {
      draftState.isLoading = action.payload;
    },
    setError(draftState, action: PayloadAction<string | null>) {
      draftState.error = action.payload;
      draftState.isLoading = false;
    },
    loginSuccess(draftState, action: PayloadAction<OtpVerifyResponse>) {
      draftState.isAuthenticated = true;
      draftState.user = action.payload.user_data;
      draftState.token = action.payload.token_data.access_token;
      draftState.isLoading = false;
      draftState.error = null;
    },
    logout(draftState) {
      draftState.isAuthenticated = false;
      draftState.user = null;
      draftState.token = null;
      draftState.emailToken = null;
      draftState.isLoading = false;
      draftState.error = null;
    },
    clearError(draftState) {
      draftState.error = null;
    },
  },
});

// External Auth API - Inject into baseApi to use dynamic base query
// Now uses real backend endpoints consistently (no more mocking)
export const externalAuthApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    requestOtp: build.mutation<OtpRequestResponse, OtpRequestPayload>({
      query: (data) => ({
        url: "plus/external-login/request-otp",
        method: "POST",
        body: data,
      }),
    }),
    verifyOtp: build.mutation<OtpVerifyResponse, OtpVerifyPayload>({
      query: (data) => ({
        url: "plus/external-login/verify-otp",
        method: "POST",
        body: data,
      }),
    }),
  }),
});

// Action creators
export const {
  setEmailToken,
  setLoading,
  setError,
  loginSuccess,
  logout,
  clearError,
} = externalAuthSlice.actions;

// Selectors
export const selectExternalAuth = (state: {
  externalAuth: ExternalAuthState;
}) => state.externalAuth;
export const selectExternalUser = (state: {
  externalAuth: ExternalAuthState;
}) => selectExternalAuth(state).user;
export const selectExternalToken = (state: {
  externalAuth: ExternalAuthState;
}) => selectExternalAuth(state).token;
export const selectExternalAuthLoading = (state: {
  externalAuth: ExternalAuthState;
}) => selectExternalAuth(state).isLoading;
export const selectExternalAuthError = (state: {
  externalAuth: ExternalAuthState;
}) => selectExternalAuth(state).error;
export const selectIsExternalAuthenticated = (state: {
  externalAuth: ExternalAuthState;
}) => selectExternalAuth(state).isAuthenticated;
export const selectEmailToken = (state: { externalAuth: ExternalAuthState }) =>
  selectExternalAuth(state).emailToken;

// API hooks
export const { useRequestOtpMutation, useVerifyOtpMutation } = externalAuthApi;

// Reducer export
export const { reducer } = externalAuthSlice;
export const externalAuthReducer = externalAuthSlice.reducer;
