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

import styles from "./AuthFormLayout.module.scss";

interface AuthFormLayoutProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
  dataTestId?: string;
}

export const AuthFormLayout = ({
  children,
  title,
  className,
  dataTestId = "auth-form-layout",
}: AuthFormLayoutProps) => {
  const config = useConfig();

  return (
    <Flex
      justify="center"
      align="center"
      data-testid={dataTestId}
      className={[styles.root, className].filter(Boolean).join(" ")}
    >
      <div className={styles.container}>
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
            {/* Form Box */}
            <div className={styles.formBox}>
              <Space direction="vertical" size={32} style={{ width: "100%" }}>
                {title && (
                  <div>
                    <Space
                      direction="vertical"
                      size={16}
                      style={{ width: "100%" }}
                    >
                      <Flex justify="center">
                        <Typography.Title level={2} className={styles.title}>
                          {title}
                        </Typography.Title>
                      </Flex>
                    </Space>
                  </div>
                )}

                {/* Form Content */}
                <div className={styles.formContent}>{children}</div>
              </Space>
            </div>
          </Space>
        </Space>
      </div>
    </Flex>
  );
};
