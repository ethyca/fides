"use client";

import {
  AntAlert as Alert,
  AntButton as Button,
  AntSpace as Space,
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
      // eslint-disable-next-line no-console
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
    <div data-testid="otp-request-form">
      <Space direction="vertical" size={24} style={{ width: "100%" }}>
        <div style={{ textAlign: "center" }}>
          <Space direction="vertical" size={8}>
            <Typography.Title level={3} style={{ marginBottom: 0 }}>
              Request Access Code
            </Typography.Title>
            <Typography.Text type="secondary">
              We&apos;ll send a verification code to your email address
            </Typography.Text>
          </Space>
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

        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <div>
            <Typography.Text strong>Email Address:</Typography.Text>
            <div style={{ marginTop: "4px" }}>
              <Typography.Text
                data-testid="otp-request-email-display"
                style={{ fontSize: "18px" }}
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
        </Space>

        <div style={{ textAlign: "center" }}>
          <Typography.Text type="secondary" style={{ fontSize: "14px" }}>
            The verification code will be sent to your email and is valid for 10
            minutes.
          </Typography.Text>
        </div>
      </Space>
    </div>
  );
};

export default OtpRequestForm;
