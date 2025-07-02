/**
 * External Task Layout Component
 *
 * This component provides the layout for external users to view and manage their tasks.
 * It includes a header with user information, logout functionality, and the tasks table.
 */

import {
  AntButton as Button,
  AntCard as Card,
  AntFlex as Flex,
  AntTypography as Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import Image from "next/image";

import BrandLink from "~/components/BrandLink";
import { useConfig } from "~/features/common/config.slice";
import { useSettings } from "~/features/common/settings.slice";

import {
  logout,
  selectExternalUser,
  selectIsExternalAuthenticated,
} from "../external-auth.slice";
import { useExternalAppDispatch, useExternalAppSelector } from "../hooks";
import { ExternalManualTasks } from "./ExternalManualTasks";

export const ExternalTaskLayout = () => {
  const dispatch = useExternalAppDispatch();
  const user = useExternalAppSelector(selectExternalUser);
  const isAuthenticated = useExternalAppSelector(selectIsExternalAuthenticated);
  const config = useConfig();
  const { SHOW_BRAND_LINK } = useSettings();

  // If not authenticated, don't render anything (parent should handle this)
  if (!isAuthenticated || !user) {
    return null;
  }

  const handleLogout = () => {
    dispatch(logout());
  };

  const displayName =
    `${user.first_name || ""} ${user.last_name || ""}`.trim() ||
    user.email_address ||
    "User";

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: palette.FIDESUI_NEUTRAL_75,
        padding: "32px 16px",
        position: "relative",
      }}
      data-testid="external-task-layout"
    >
      <div style={{ margin: "0 auto", width: "100%", padding: "0 24px" }}>
        <Flex vertical gap={24} style={{ width: "100%" }}>
          {/* Header */}
          <Card>
            <Flex justify="space-between" align="center">
              {/* Left side - Logo and Title */}
              <Flex align="center" gap={32}>
                <Image
                  src={config?.logo_path || "/logo.svg"}
                  alt="Fides logo"
                  width={205}
                  height={46}
                  priority
                />
                <div>
                  <Typography.Title
                    level={2}
                    style={{ marginBottom: "8px" }}
                    data-testid="external-task-header"
                  >
                    My Tasks
                  </Typography.Title>
                  <Typography.Text
                    type="secondary"
                    data-testid="external-user-info"
                  >
                    Welcome, {displayName}
                  </Typography.Text>
                </div>
              </Flex>

              {/* Right side - Logout button */}
              <div>
                <Button
                  onClick={handleLogout}
                  data-testid="external-logout-button"
                  aria-label="Logout"
                >
                  Logout
                </Button>
              </div>
            </Flex>
          </Card>

          {/* Tasks Content */}
          <Card>
            <ExternalManualTasks />
          </Card>
        </Flex>
      </div>

      {/* Brand Link - positioned in bottom right if enabled */}
      {SHOW_BRAND_LINK && (
        <BrandLink
          position="fixed"
          right={6}
          bottom={6}
          data-testid="external-brand-link"
        />
      )}
    </div>
  );
};
