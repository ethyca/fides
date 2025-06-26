/**
 * External Authentication Slice
 *
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/auth/auth.slice.ts
 *
 * Key differences for external users:
 * - Two-step authentication (request OTP + verify OTP)
 * - Uses external-login endpoints from endpoint-design.md
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

// Check if we're in a test environment (Cypress)
const isTestEnvironment = () => {
  const result =
    typeof window !== "undefined" &&
    (window.Cypress || process.env.NODE_ENV === "test");

  if (process.env.NODE_ENV === "development") {
    // eslint-disable-next-line no-console
    console.log("🔍 isTestEnvironment result:", {
      result,
      windowExists: typeof window !== "undefined",
      hasCypress: typeof window !== "undefined" && !!window.Cypress,
      nodeEnv: process.env.NODE_ENV,
    });
  }

  return result;
};

// External Auth API - Inject into baseApi to use dynamic base query
export const externalAuthApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    requestOtp: build.mutation<OtpRequestResponse, OtpRequestPayload>({
      // Use real API call in test environment, mock otherwise
      ...(isTestEnvironment()
        ? {
            query: (data) => ({
              url: "external-login/request-otp",
              method: "POST",
              body: data,
            }),
          }
        : {
            queryFn: async () => {
              // Mock response for development
              await new Promise<void>((resolve) => {
                setTimeout(() => resolve(), 500);
              });
              return {
                data: {
                  message: "OTP code sent to email",
                  email: "john.doe@example.com",
                },
              };
            },
          }),
    }),
    verifyOtp: build.mutation<OtpVerifyResponse, OtpVerifyPayload>({
      // Use real API call in test environment, mock otherwise
      ...(isTestEnvironment()
        ? {
            query: (data) => ({
              url: "external-login/verify-otp",
              method: "POST",
              body: data,
            }),
          }
        : {
            queryFn: async () => {
              // Mock response for development
              await new Promise<void>((resolve) => {
                setTimeout(() => resolve(), 500);
              });
              return {
                data: {
                  user_data: {
                    id: "ext_user_123",
                    username: "john.doe.external",
                    created_at: "2025-06-17T20:17:08.391Z",
                    email_address: "john.doe@example.com",
                    first_name: "John",
                    last_name: "Doe",
                    disabled: false,
                    disabled_reason: "",
                  },
                  token_data: {
                    access_token: "ext_token_abc123def456",
                  },
                },
              };
            },
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
