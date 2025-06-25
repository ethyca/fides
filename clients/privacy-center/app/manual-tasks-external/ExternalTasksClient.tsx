"use client";

import { AntTypography as Typography } from "fidesui";
import React, { useState } from "react";

import OtpRequestForm from "~/features/external-manual-tasks/components/OtpRequestForm";
import OtpVerificationForm from "~/features/external-manual-tasks/components/OtpVerificationForm";
import {
  ExternalUser,
  OtpVerifyResponse,
} from "~/features/external-manual-tasks/types";
import { NextSearchParams } from "~/types/next";

interface ExternalTasksClientProps {
  searchParams: NextSearchParams;
}

type AuthStep = "request-otp" | "verify-otp" | "authenticated";

/**
 * Client component for the external manual tasks page.
 * Handles the OTP authentication flow and task management UI.
 */
const ExternalTasksClient = ({ searchParams }: ExternalTasksClientProps) => {
  const resolvedSearchParams = React.use(searchParams);
  const token = resolvedSearchParams?.token as string;

  const [authStep, setAuthStep] = useState<AuthStep>("request-otp");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authenticatedUser, setAuthenticatedUser] =
    useState<ExternalUser | null>(null);

  const handleOtpRequested = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // TODO: Replace with actual API call
      // await requestOtp({ email_token: token });

      // Simulate API call
      await new Promise<void>((resolve) => setTimeout(resolve, 1000));

      setAuthStep("verify-otp");
    } catch (err) {
      setError("Failed to send verification code. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpVerified = async (response: OtpVerifyResponse) => {
    setIsLoading(true);
    setError(null);

    try {
      // TODO: Store auth token and user data in Redux
      setAuthenticatedUser(response.user_data);
      setAuthStep("authenticated");
    } catch (err) {
      setError("Failed to verify code. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToRequest = () => {
    setAuthStep("request-otp");
    setError(null);
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
        return (
          <div data-testid="external-task-layout">
            <Typography.Title level={3}>
              Welcome, {authenticatedUser?.first_name}!
            </Typography.Title>
            <Typography.Text>
              Authentication successful. Task management UI will be implemented
              next.
            </Typography.Text>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-gray-50"
      data-testid="external-auth-container"
    >
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Typography.Title level={2}>External Manual Tasks</Typography.Title>
          {process.env.NODE_ENV === "development" && (
            <Typography.Text type="secondary" className="text-xs">
              Token: {token}
            </Typography.Text>
          )}
        </div>

        {renderAuthContent()}
      </div>
    </div>
  );
};

export default ExternalTasksClient;
