"use client";

import {
  AntAlert as Alert,
  AntSpace as Space,
  AntTypography as Typography,
} from "fidesui";
import React from "react";

/**
 * NoAccessTokenMessage Component
 *
 * Displays a message when users try to access the external tasks portal
 * without a valid access token (either by reloading the page or accessing directly).
 * Explains that they need to use the original link from their invitation email.
 */
const NoAccessTokenMessage = () => {
  return (
    <div data-testid="no-access-token-message">
      <Space direction="vertical" size={24} style={{ width: "100%" }}>
        <div style={{ textAlign: "center" }}>
          <Space direction="vertical" size={8}>
            <Typography.Title level={3} style={{ marginBottom: 0 }}>
              Access Required
            </Typography.Title>
          </Space>
        </div>

        <Alert
          type="info"
          showIcon
          message="Please use your invitation link"
          description={
            <Space direction="vertical" size={8}>
              <Typography.Text>
                To access the external tasks portal, you need to use the
                original link from your invitation email.
              </Typography.Text>
            </Space>
          }
          style={{ textAlign: "left" }}
        />

        <div style={{ textAlign: "center" }}>
          <Typography.Text type="secondary" style={{ fontSize: "14px" }}>
            The invitation link contains a secure access token that is required
            to use this portal.
          </Typography.Text>
        </div>
      </Space>
    </div>
  );
};

export default NoAccessTokenMessage;
