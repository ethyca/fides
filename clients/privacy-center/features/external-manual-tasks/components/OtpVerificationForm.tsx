"use client";

import {
  AntAlert as Alert,
  AntButton as Button,
  AntInput as Input,
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
    <div className="space-y-4" data-testid="otp-verification-form">
      <div className="text-center space-y-2">
        <Typography.Title level={3}>Enter Verification Code</Typography.Title>
        <Typography.Text type="secondary">
          Please enter the 6-digit code sent to your email
        </Typography.Text>
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

      <div className="space-y-4">
        <div>
          <Typography.Text strong>Verification Code:</Typography.Text>
          <div className="mt-2">
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
          <div className="mt-1">
            <Typography.Text type="secondary" className="text-sm">
              Enter the 6-digit code from your email
            </Typography.Text>
          </div>
        </div>

        <div className="space-y-3">
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
        </div>
      </div>

      <div className="text-center">
        <Typography.Text type="secondary" className="text-sm">
          Didn&apos;t receive the code? Check your spam folder or go back to
          request a new one.
        </Typography.Text>
      </div>
    </div>
  );
};

export default OtpVerificationForm;
