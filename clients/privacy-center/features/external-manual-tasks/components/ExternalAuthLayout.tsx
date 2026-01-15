/**
 * External Auth Layout Component
 *
 * Provides the layout for external user authentication steps (OTP request/verification).
 * Follows the admin-ui login design pattern with Fides logo and centered form box.
 */

import React from "react";

import { AuthFormLayout } from "~/components/common/AuthFormLayout";

interface ExternalAuthLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export const ExternalAuthLayout = ({
  children,
  title = "External Manual Tasks",
}: ExternalAuthLayoutProps) => {
  return (
    <AuthFormLayout
      title={title}
      maxWidth="512px"
      showTitleOnDesktop
      dataTestId="external-auth-container"
    >
      {children}
    </AuthFormLayout>
  );
};
