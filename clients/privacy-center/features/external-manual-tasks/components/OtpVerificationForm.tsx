"use client";

import {
  AntAlert as Alert,
  AntButton as Button,
  AntInput as Input,
  AntSpace as Space,
  AntTypography as Typography,
} from "fidesui";
import React, { useState } from "react";

import { loginSuccess, useVerifyOtpMutation } from "../external-auth.slice";
import { useExternalAppDispatch } from "../hooks";
import { OtpVerificationFormProps } from "../types";

/**
 * OTP Verification Form Component - Step 2 of Authentication
 *
 * Allows users to enter the OTP code they received via email.
 * This is the second step in the external user authentication flow.
 */
const OtpVerificationForm = ({
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  emailToken: _,
  onOtpVerified,
  onBack,
  isLoading = false,
  error = null,
}: OtpVerificationFormProps) => {
  const [otpCode, setOtpCode] = useState("");
  const dispatch = useExternalAppDispatch();
  const [verifyOtp, { isLoading: isMutationLoading, error: mutationError }] =
    useVerifyOtpMutation();

  const handleVerifyOtp = async () => {
    if (otpCode.trim()) {
      try {
        // For now, we'll use a placeholder email - this will be resolved from the token
        // TODO: Extract email from emailToken when backend integration is complete
        const displayEmail = "john.doe@example.com";

        const response = await verifyOtp({
          email: displayEmail,
          otp_code: otpCode,
        }).unwrap();

        // Dispatch login success to update Redux state
        dispatch(loginSuccess(response));

        onOtpVerified();
      } catch (err) {
        // Error will be handled by the mutation error state
        // eslint-disable-next-line no-console
        console.error("Failed to verify OTP:", err);
      }
    }
  };

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, "").slice(0, 6); // Only digits, max 6
    setOtpCode(value);
  };

  const isValidOtp = otpCode.length === 6;
  const isFormLoading = isLoading || isMutationLoading;
  const displayError =
    error ||
    (mutationError ? "Failed to verify code. Please try again." : null);

  return (
    <div data-testid="otp-verification-form">
      <Space direction="vertical" size={24} style={{ width: "100%" }}>
        <div style={{ textAlign: "center" }}>
          <Space direction="vertical" size={8}>
            <Typography.Title level={3} style={{ marginBottom: 0 }}>
              Enter Verification Code
            </Typography.Title>
            <Typography.Text type="secondary">
              Please enter the 6-digit code sent to your email
            </Typography.Text>
          </Space>
        </div>

        {displayError && (
          <Alert
            type="error"
            message="Verification Failed"
            description={displayError}
            showIcon
            data-testid="auth-error-message"
          />
        )}

        <Space direction="vertical" size={24} style={{ width: "100%" }}>
          <div>
            <Typography.Text strong>Verification Code:</Typography.Text>
            <div style={{ marginTop: "8px" }}>
              <Input
                size="large"
                placeholder="000000"
                value={otpCode}
                onChange={handleOtpChange}
                maxLength={6}
                style={{
                  fontSize: "24px",
                  textAlign: "center",
                  letterSpacing: "8px",
                }}
                data-testid="otp-input"
              />
            </div>
            <div style={{ marginTop: "4px" }}>
              <Typography.Text type="secondary" style={{ fontSize: "14px" }}>
                Enter the 6-digit code from your email
              </Typography.Text>
            </div>
          </div>

          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            <Button
              type="primary"
              size="large"
              block
              loading={isFormLoading}
              disabled={!isValidOtp || isFormLoading}
              onClick={handleVerifyOtp}
              data-testid="otp-verify-button"
            >
              {isFormLoading ? "Verifying..." : "Verify Code"}
            </Button>

            <Button
              type="default"
              size="large"
              block
              disabled={isFormLoading}
              onClick={onBack}
              data-testid="otp-back-button"
            >
              Back to Request Code
            </Button>
          </Space>
        </Space>

        <div style={{ textAlign: "center" }}>
          <Typography.Text type="secondary" style={{ fontSize: "14px" }}>
            Didn&apos;t receive the code? Check your spam folder or go back to
            request a new one.
          </Typography.Text>
        </div>
      </Space>
    </div>
  );
};

export default OtpVerificationForm;
