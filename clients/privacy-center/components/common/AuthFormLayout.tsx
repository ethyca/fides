/* eslint-disable @next/next/no-img-element */

"use client";

/**
 * Shared Auth Form Layout Component
 *
 * Provides a reusable full-page layout for authentication and form flows.
 * Used by both ExternalAuthLayout and PrivacyRequestLayout to avoid duplication.
 */

import { Flex, Space, Typography } from "fidesui";
import React from "react";

import { useConfig } from "~/features/common/config.slice";

interface AuthFormLayoutProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
  showTitleOnDesktop?: boolean;
  dataTestId?: string;
}

export const AuthFormLayout = ({
  children,
  title,
  className = "max-w-[640px]",
  showTitleOnDesktop = true,
  dataTestId = "auth-form-layout",
}: AuthFormLayoutProps) => {
  const config = useConfig();

  return (
    <Flex
      justify="center"
      align="center"
      className="w-full min-h-screen bg-neutral-75 p-4"
      data-testid={dataTestId}
    >
      <div className={`w-full p-6 ${className}`}>
        <Space direction="vertical" size={48} className="w-full">
          {/* Logo */}
          <Flex justify="center">
            <img
              src={config?.logo_path || "/logo.svg"}
              alt="Logo"
              width={205}
              height={46}
            />
          </Flex>

          {/* Form Container */}
          <div className="bg-white rounded-md shadow-sm p-6 w-full">
            {title && (
              <Space direction="vertical" size={16} className="w-full mb-8">
                {/* Desktop Title - conditionally shown */}
                {showTitleOnDesktop && (
                  <Flex justify="center">
                    <Typography.Title
                      level={2}
                      className="text-2xl text-minos mb-0 text-center"
                    >
                      {title}
                    </Typography.Title>
                  </Flex>
                )}
              </Space>
            )}

            {/* Content */}
            <div className="w-full">{children}</div>
          </div>
        </Space>
      </div>
    </Flex>
  );
};
