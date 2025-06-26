"use client";

import {
  AntAlert as Alert,
  AntButton as Button,
  AntTypography as Typography,
} from "fidesui";
import React from "react";

import { useRequestOtpMutation } from "../external-auth.slice";
import { OtpRequestFormProps } from "../types";

/**
 * OTP Request Form Component - Step 1 of Authentication
 *
 * Displays the user's email and allows them to request an OTP code.
 * This is the first step in the external user authentication flow.
 */
const OtpRequestForm = ({
  emailToken,
  onOtpRequested,
  isLoading = false,
  error = null,
}: OtpRequestFormProps) => {
  const [requestOtp, { isLoading: isMutationLoading, error: mutationError }] =
    useRequestOtpMutation();

  const handleRequestOtp = async () => {
    try {
      // For now, we'll use a placeholder email - this will be resolved from the token
      // TODO: Extract email from emailToken when backend integration is complete
      const displayEmail = "user@example.com";

      await requestOtp({
        email: displayEmail,
        email_token: emailToken,
      }).unwrap();

      onOtpRequested();
    } catch (err) {
      // Error will be handled by the mutation error state
      console.error("Failed to request OTP:", err);
    }
  };

  // For now, we'll show a placeholder email - this will be resolved from the token
  // TODO: Extract email from emailToken when backend integration is complete
  const displayEmail = "user@example.com";

  const isFormLoading = isLoading || isMutationLoading;
  const displayError =
    error ||
    (mutationError
      ? "Failed to send verification code. Please try again."
      : null);

  return (
    <div className="space-y-4" data-testid="otp-request-form">
      <div className="text-center space-y-2">
        <Typography.Title level={3}>Request Access Code</Typography.Title>
        <Typography.Text type="secondary">
          We&apos;ll send a verification code to your email address
        </Typography.Text>
      </div>

      {displayError && (
        <Alert
          type="error"
          message="Authentication Error"
          description={displayError}
          showIcon
          data-testid="auth-error-message"
        />
      )}

      <div className="space-y-3">
        <div>
          <Typography.Text strong>Email Address:</Typography.Text>
          <div className="mt-1">
            <Typography.Text
              data-testid="otp-request-email-display"
              className="text-lg"
            >
              {displayEmail}
            </Typography.Text>
          </div>
        </div>

        <Button
          type="primary"
          size="large"
          block
          loading={isFormLoading}
          onClick={handleRequestOtp}
          data-testid="otp-request-button"
        >
          {isFormLoading ? "Sending..." : "Send Verification Code"}
        </Button>
      </div>

      <div className="text-center">
        <Typography.Text type="secondary" className="text-sm">
          The verification code will be sent to your email and is valid for 10
          minutes.
        </Typography.Text>
      </div>
    </div>
  );
};

export default OtpRequestForm;
