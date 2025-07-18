"use client";

import { AntMessage as message } from "fidesui";
import React, { useEffect } from "react";

import { useConfig } from "~/features/common/config.slice";
import { useSettings } from "~/features/common/settings.slice";
import { ExternalAuthLayout } from "~/features/external-manual-tasks/components/ExternalAuthLayout";
import { ExternalTaskLayout } from "~/features/external-manual-tasks/components/ExternalTaskLayout";
import NoAccessTokenMessage from "~/features/external-manual-tasks/components/NoAccessTokenMessage";
import OtpRequestForm from "~/features/external-manual-tasks/components/OtpRequestForm";
import OtpVerificationForm from "~/features/external-manual-tasks/components/OtpVerificationForm";
import {
  loginSuccess,
  selectEmailToken,
  selectExternalAuthError,
  selectExternalAuthLoading,
  selectExternalUser,
  selectIsExternalAuthenticated,
  setEmailToken,
} from "~/features/external-manual-tasks/external-auth.slice";
import {
  useRequestOtpMutation,
  useVerifyOtpMutation,
} from "~/features/external-manual-tasks/external-auth-api.slice";
import ExternalStoreProvider from "~/features/external-manual-tasks/ExternalStoreProvider";
import {
  useExternalAppDispatch,
  useExternalAppSelector,
} from "~/features/external-manual-tasks/hooks";
import { NextSearchParams } from "~/types/next";

interface ExternalTasksClientProps {
  searchParams: NextSearchParams;
}

type AuthStep = "request-otp" | "verify-otp" | "authenticated";

/**
 * Client component for the external manual tasks page.
 * Handles the OTP authentication flow and task management UI.
 * Centralizes all authentication logic using Redux slice hooks.
 */
const ExternalTasksClientInner = ({
  searchParams,
}: ExternalTasksClientProps) => {
  const resolvedSearchParams = React.use(searchParams);
  const token = resolvedSearchParams?.access_token as string;

  const dispatch = useExternalAppDispatch();

  // Redux selectors
  const authenticatedUser = useExternalAppSelector(selectExternalUser);
  const isAuthenticated = useExternalAppSelector(selectIsExternalAuthenticated);
  const isLoading = useExternalAppSelector(selectExternalAuthLoading);
  const error = useExternalAppSelector(selectExternalAuthError);
  const emailToken = useExternalAppSelector(selectEmailToken);

  // Authentication mutations
  const [requestOtp, { isLoading: isRequestingOtp, error: requestOtpError }] =
    useRequestOtpMutation();
  const [verifyOtp, { isLoading: isVerifyingOtp, error: verifyOtpError }] =
    useVerifyOtpMutation();

  const [authStep, setAuthStep] = React.useState<AuthStep>("request-otp");
  const [enteredEmail, setEnteredEmail] = React.useState<string>("");

  // Set email token when component mounts
  useEffect(() => {
    if (token) {
      dispatch(setEmailToken(token));
    }
  }, [token, dispatch]);

  // Remove access_token from URL history to prevent storing sensitive data
  useEffect(() => {
    if (typeof window !== "undefined" && token) {
      const currentUrl = new URL(window.location.href);
      const urlParams = new URLSearchParams(currentUrl.search);

      // Check if access_token exists in the current URL
      if (urlParams.has("access_token")) {
        // Remove the access_token parameter
        urlParams.delete("access_token");

        // Build the new URL without the access_token
        const newUrl = `${currentUrl.pathname}${urlParams.toString() ? `?${urlParams.toString()}` : ""}`;

        // Update the URL without adding a new history entry
        window.history.replaceState(null, "", newUrl);
      }
    }
  }, [token]); // Run when token changes

  // Update auth step based on authentication state
  useEffect(() => {
    if (isAuthenticated && authenticatedUser) {
      setAuthStep("authenticated");
    } else if (!isAuthenticated) {
      // Reset to request-otp when user logs out
      setAuthStep("request-otp");
      setEnteredEmail(""); // Clear email when logging out
    }
  }, [isAuthenticated, authenticatedUser]);

  // Centralized OTP request handler
  const handleRequestOtp = async (email: string) => {
    if (!emailToken) {
      message.error("Email token not available");
      return;
    }

    try {
      await requestOtp({
        email,
        email_token: emailToken,
      }).unwrap();

      // Store the email that was used for the OTP request
      setEnteredEmail(email);
      setAuthStep("verify-otp");
    } catch (err) {
      message.error("Failed to request OTP. Please try again.");
      // Error will be shown via Redux state
    }
  };

  // Centralized OTP verification handler
  const handleVerifyOtp = async (otpCode: string) => {
    // Use the same email that was entered in the request form
    if (!enteredEmail) {
      message.error("No email address available for verification");
      return;
    }

    try {
      const response = await verifyOtp({
        email: enteredEmail,
        otp_code: otpCode,
      }).unwrap();

      // Dispatch login success to update Redux state
      dispatch(loginSuccess(response));

      setAuthStep("authenticated");
    } catch (err) {
      message.error("Failed to verify OTP. Please try again.");
      // Error will be shown via Redux state
    }
  };

  const handleBackToRequest = () => {
    setAuthStep("request-otp");
    // Keep the email when going back so user doesn't have to re-enter it
  };

  // Combine all loading states
  const combinedLoading = isLoading || isRequestingOtp || isVerifyingOtp;

  // Combine all error states
  const combinedError =
    error ||
    (requestOtpError
      ? "Failed to send verification code. Please try again."
      : null) ||
    (verifyOtpError ? "Failed to verify code. Please try again." : null);

  const renderAuthContent = () => {
    // If user is authenticated, show authenticated content regardless of token
    if (authStep === "authenticated") {
      return <ExternalTaskLayout />;
    }

    // For non-authenticated users, require token
    if (!token) {
      return <NoAccessTokenMessage />;
    }

    switch (authStep) {
      case "request-otp":
        return (
          <OtpRequestForm
            emailToken={emailToken || ""}
            onRequestOtp={handleRequestOtp}
            initialEmail={enteredEmail}
            isLoading={combinedLoading}
            error={combinedError}
          />
        );

      case "verify-otp":
        return (
          <OtpVerificationForm
            emailToken={emailToken || ""}
            enteredEmail={enteredEmail}
            onVerifyOtp={handleVerifyOtp}
            onBack={handleBackToRequest}
            isLoading={combinedLoading}
            error={combinedError}
          />
        );

      default:
        return null;
    }
  };

  // For authenticated state, render the full-width layout
  if (authStep === "authenticated") {
    return renderAuthContent();
  }

  // For auth steps, render centered layout
  return (
    <ExternalAuthLayout title="External task portal">
      {renderAuthContent()}
    </ExternalAuthLayout>
  );
};

// Wrapper component with Redux provider
const ExternalTasksClient = ({ searchParams }: ExternalTasksClientProps) => {
  const settings = useSettings(); // Get settings from main store
  const config = useConfig(); // Config should be available from server component

  return (
    <ExternalStoreProvider settings={settings} config={config}>
      <ExternalTasksClientInner searchParams={searchParams} />
    </ExternalStoreProvider>
  );
};

export default ExternalTasksClient;
