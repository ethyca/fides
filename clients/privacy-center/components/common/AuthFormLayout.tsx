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
  dataTestId?: string;
}

export const AuthFormLayout = ({
  children,
  title,
  className = "max-w-[640px]",
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
      }}
      data-testid={dataTestId}
      className={className}
    >
      <div style={{ width: "100%", maxWidth: "512px", padding: "48px 24px" }}>
        <Space direction="vertical" size={64} style={{ width: "100%" }}>
          {/* Fides Logo */}
          <Flex justify="center">
            <img
              src={config?.logo_path || "/logo.svg"}
              alt="Logo"
              width={205}
              height={46}
              data-testid="logo"
            />
          </Flex>

          {/* Title and Form Container */}
          <Space direction="vertical" size={24} style={{ width: "100%" }}>
            {/* Title - Hidden on mobile, shown on desktop */}
            {title && (
              <div style={{ display: "none" }}>
                <Flex justify="center">
                  <Typography.Title
                    level={1}
                    style={{
                      fontSize: "2.25rem", // 4xl
                      color: "#2b2e35", // minos
                      marginBottom: 0,
                    }}
                  >
                    {title}
                  </Typography.Title>
                </Flex>
              </div>
            )}
            {/* Form Box */}
            <div
              style={{
                backgroundColor: "white",
                padding: "48px",
                width: "100%",
                maxWidth: "640px",
                margin: "0 auto",
                borderRadius: "4px",
                boxShadow:
                  "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
              }}
            >
              <Space direction="vertical" size={32} style={{ width: "100%" }}>
                {/* Mobile Title - Shown on mobile, hidden on desktop */}
                {title && (
                  <div>
                    <Space
                      direction="vertical"
                      size={16}
                      style={{ width: "100%" }}
                    >
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
                    </Space>
                  </div>
                )}

                {/* Form Content */}
                <div style={{ width: "100%" }}>{children}</div>
              </Space>
            </div>
          </Space>
        </Space>
      </div>
    </Flex>
  );
};
