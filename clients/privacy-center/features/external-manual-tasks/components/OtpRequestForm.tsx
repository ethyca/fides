"use client";

import {
  AntAlert as Alert,
  AntButton as Button,
  AntInput as Input,
  AntSpace as Space,
  AntTypography as Typography,
} from "fidesui";
import React, { useEffect, useState } from "react";

import { OtpRequestFormProps } from "../types";

/**
 * OTP Request Form Component - Step 1 of Authentication
 *
 * Displays an email input field and allows users to request an OTP code.
 * This is the first step in the external user authentication flow.
 * Now purely presentational - authentication logic is handled by parent.
 */
const OtpRequestForm = ({
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  emailToken: _,
  onRequestOtp,
  initialEmail = "",
  isLoading = false,
  error = null,
}: OtpRequestFormProps) => {
  const [email, setEmail] = useState(initialEmail);
  const [emailError, setEmailError] = useState<string | null>(null);

  // Update email when initialEmail changes (when going back from verification)
  useEffect(() => {
    setEmail(initialEmail);
  }, [initialEmail]);

  // Simple email validation
  const validateEmail = (emailValue: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(emailValue);
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;
    setEmail(value);

    // Clear email error when user starts typing
    if (emailError) {
      setEmailError(null);
    }
  };

  const handleRequestOtp = async () => {
    // Validate email before sending request
    if (!email.trim()) {
      setEmailError("Email address is required");
      return;
    }

    if (!validateEmail(email.trim())) {
      setEmailError("Please enter a valid email address");
      return;
    }

    // Clear any previous email errors
    setEmailError(null);

    await onRequestOtp(email.trim());
  };

  const isValidEmail = email.trim() && validateEmail(email.trim());

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

        {error && (
          <Alert
            type="error"
            message="Authentication Error"
            description={error}
            showIcon
            data-testid="auth-error-message"
          />
        )}

        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <div>
            <Typography.Text strong>Email Address:</Typography.Text>
            <div style={{ marginTop: "8px" }}>
              <Input
                size="large"
                type="email"
                placeholder="Enter your email address"
                value={email}
                onChange={handleEmailChange}
                disabled={isLoading}
                status={emailError ? "error" : undefined}
                data-testid="otp-request-email-input"
              />
              {emailError && (
                <div style={{ marginTop: "4px" }}>
                  <Typography.Text type="danger" style={{ fontSize: "14px" }}>
                    {emailError}
                  </Typography.Text>
                </div>
              )}
            </div>
          </div>

          <Button
            type="primary"
            size="large"
            block
            loading={isLoading}
            disabled={!isValidEmail || isLoading}
            onClick={handleRequestOtp}
            data-testid="otp-request-button"
          >
            {isLoading ? "Sending..." : "Send Verification Code"}
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
