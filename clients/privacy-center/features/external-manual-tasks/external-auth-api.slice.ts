/**
 * External Authentication API Slice
 *
 * Separated from external-auth.slice.ts to use externalBaseApi with proper authentication
 * FIXES: Authentication token issue where baseApi didn't know about external auth tokens
 */

import { externalBaseApi } from "./external-base-api.slice";
import {
  OtpRequestPayload,
  OtpRequestResponse,
  OtpVerifyPayload,
  OtpVerifyResponse,
} from "./types";

// External Auth API - Inject into externalBaseApi to use proper authentication
export const externalAuthApi = externalBaseApi.injectEndpoints({
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

// API hooks
export const { useRequestOtpMutation, useVerifyOtpMutation } = externalAuthApi;
