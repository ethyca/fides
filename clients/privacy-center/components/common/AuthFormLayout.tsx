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
  maxWidth?: string;
  showTitleOnDesktop?: boolean;
  dataTestId?: string;
}

export const AuthFormLayout = ({
  children,
  title,
  maxWidth = "640px",
  showTitleOnDesktop = true,
  dataTestId = "auth-form-layout",
}: AuthFormLayoutProps) => {
  const config = useConfig();

  return (
    <Flex
      justify="center"
      align="center"
      style={{
        width: "100%",
        minHeight: "100vh",
        backgroundColor: "#f5f5f5", // neutral-75 from palette
        padding: "32px 16px",
      }}
      data-testid={dataTestId}
    >
      <div style={{ width: "100%", maxWidth, padding: "48px 24px" }}>
        <Space direction="vertical" size={48} style={{ width: "100%" }}>
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
          <div
            style={{
              backgroundColor: "white",
              padding: "48px",
              width: "100%",
              borderRadius: "4px",
              boxShadow:
                "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
            }}
          >
            {title && (
              <Space
                direction="vertical"
                size={16}
                style={{ width: "100%", marginBottom: "32px" }}
              >
                {/* Desktop Title - conditionally shown */}
                {showTitleOnDesktop && (
                  <Flex justify="center">
                    <Typography.Title
                      level={2}
                      style={{
                        fontSize: "1.875rem", // 3xl
                        color: "#2b2e35", // minos
                        marginBottom: 0,
                        textAlign: "center",
                      }}
                    >
                      {title}
                    </Typography.Title>
                  </Flex>
                )}
              </Space>
            )}

            {/* Content */}
            <div style={{ width: "100%" }}>{children}</div>
          </div>
        </Space>
      </div>
    </Flex>
  );
};
