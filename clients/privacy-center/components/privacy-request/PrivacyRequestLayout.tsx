import React from "react";

import { AuthFormLayout } from "~/components/common/AuthFormLayout";

interface PrivacyRequestLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export const PrivacyRequestLayout = ({
  children,
  title,
}: PrivacyRequestLayoutProps) => {
  return (
    <AuthFormLayout
      title={title}
      maxWidth="640px"
      showTitleOnDesktop
      dataTestId="privacy-request-layout"
    >
      {children}
    </AuthFormLayout>
  );
};
