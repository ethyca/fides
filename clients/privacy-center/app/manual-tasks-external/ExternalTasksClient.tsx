"use client";

import { AntButton as Button, AntTypography as Typography } from "fidesui";
import React from "react";

import { NextSearchParams } from "~/types/next";

interface ExternalTasksClientProps {
  searchParams: NextSearchParams;
}

/**
 * Client component for the external manual tasks page.
 * Handles the OTP authentication flow and task management UI.
 */
const ExternalTasksClient = ({ searchParams }: ExternalTasksClientProps) => {
  const resolvedSearchParams = React.use(searchParams);
  const token = resolvedSearchParams?.token;

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-gray-50"
      data-testid="external-auth-container"
    >
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Typography.Title level={2}>External Manual Tasks</Typography.Title>
          <Typography.Text type="secondary">Token: {token}</Typography.Text>
        </div>
        <div className="space-y-4" data-testid="otp-request-form">
          <Typography.Text data-testid="otp-request-email-display">
            user@example.com
          </Typography.Text>
          <Button
            type="primary"
            size="large"
            block
            data-testid="otp-request-button"
          >
            Send OTP
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ExternalTasksClient;
