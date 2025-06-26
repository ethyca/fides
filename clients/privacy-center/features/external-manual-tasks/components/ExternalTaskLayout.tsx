/**
 * External Task Layout Component
 *
 * This component provides the layout for external users to view and manage their tasks.
 * It includes a header with user information, logout functionality, and the tasks table.
 */

import {
  AntButton as Button,
  AntCard as Card,
  AntSpace as Space,
  AntTypography as Typography,
} from "fidesui";

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
        backgroundColor: "#f5f5f5", // neutral-75 from palette
        padding: "32px 16px",
      }}
      data-testid="external-task-layout"
    >
      <div className="mx-auto w-full px-6">
        <Space direction="vertical" size={24} style={{ width: "100%" }}>
          {/* Header */}
          <div
            style={{
              backgroundColor: "white",
              borderRadius: "8px",
              padding: "24px",
              boxShadow:
                "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
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
              <div>
                <Button
                  onClick={handleLogout}
                  data-testid="external-logout-button"
                  aria-label="Logout"
                >
                  Logout
                </Button>
              </div>
            </div>
          </div>

          {/* Tasks Content */}
          <Card>
            <ExternalManualTasks />
          </Card>
        </Space>
      </div>
    </div>
  );
};
