"use client";

import { AntTypography as Typography } from "fidesui";
import React, { useEffect } from "react";

import { useSettings } from "~/features/common/settings.slice";
import { ExternalAuthLayout } from "~/features/external-manual-tasks/components/ExternalAuthLayout";
import { ExternalTaskLayout } from "~/features/external-manual-tasks/components/ExternalTaskLayout";
import OtpRequestForm from "~/features/external-manual-tasks/components/OtpRequestForm";
import OtpVerificationForm from "~/features/external-manual-tasks/components/OtpVerificationForm";
import {
  selectExternalAuthError,
  selectExternalAuthLoading,
  selectExternalUser,
  selectIsExternalAuthenticated,
  setEmailToken,
} from "~/features/external-manual-tasks/external-auth.slice";
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
 */
const ExternalTasksClientInner = ({
  searchParams,
}: ExternalTasksClientProps) => {
  const resolvedSearchParams = React.use(searchParams);
  const token = resolvedSearchParams?.token as string;

  const dispatch = useExternalAppDispatch();
  const authenticatedUser = useExternalAppSelector(selectExternalUser);
  const isAuthenticated = useExternalAppSelector(selectIsExternalAuthenticated);
  const isLoading = useExternalAppSelector(selectExternalAuthLoading);
  const error = useExternalAppSelector(selectExternalAuthError);

  const [authStep, setAuthStep] = React.useState<AuthStep>("request-otp");

  // Set email token when component mounts
  useEffect(() => {
    if (token) {
      dispatch(setEmailToken(token));
    }
  }, [token, dispatch]);

  // Update auth step based on authentication state
  useEffect(() => {
    if (isAuthenticated && authenticatedUser) {
      setAuthStep("authenticated");
    } else if (!isAuthenticated) {
      // Reset to request-otp when user logs out
      setAuthStep("request-otp");
    }
  }, [isAuthenticated, authenticatedUser]);

  const handleOtpRequested = () => {
    setAuthStep("verify-otp");
  };

  const handleOtpVerified = () => {
    // This will be handled by the Redux action in the component
    setAuthStep("authenticated");
  };

  const handleBackToRequest = () => {
    setAuthStep("request-otp");
  };

  const renderAuthContent = () => {
    switch (authStep) {
      case "request-otp":
        return (
          <OtpRequestForm
            emailToken={token}
            onOtpRequested={handleOtpRequested}
            isLoading={isLoading}
            error={error}
          />
        );

      case "verify-otp":
        return (
          <OtpVerificationForm
            emailToken={token}
            onOtpVerified={handleOtpVerified}
            onBack={handleBackToRequest}
            isLoading={isLoading}
            error={error}
          />
        );

      case "authenticated":
        return <ExternalTaskLayout />;

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
    <ExternalAuthLayout title="External Manual Tasks">
      {process.env.NODE_ENV === "development" && (
        <div style={{ textAlign: "center", marginBottom: "16px" }}>
          <Typography.Text type="secondary" style={{ fontSize: "12px" }}>
            Token: {token}
          </Typography.Text>
        </div>
      )}
      {renderAuthContent()}
    </ExternalAuthLayout>
  );
};

// Wrapper component with Redux provider
const ExternalTasksClient = ({ searchParams }: ExternalTasksClientProps) => {
  const settings = useSettings(); // Get settings from main store

  return (
    <ExternalStoreProvider settings={settings}>
      <ExternalTasksClientInner searchParams={searchParams} />
    </ExternalStoreProvider>
  );
};

export default ExternalTasksClient;
