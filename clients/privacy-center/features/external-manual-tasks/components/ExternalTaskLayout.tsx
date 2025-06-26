/**
 * External Task Layout Component
 *
 * This component provides the layout for external users to view and manage their tasks.
 * It includes a header with user information, logout functionality, and the tasks table.
 */

import { AntButton as Button, AntTypography as Typography } from "fidesui";

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
      className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8"
      data-testid="external-task-layout"
    >
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white shadow rounded-lg mb-6 p-6">
          <div className="flex items-center justify-between">
            <div>
              <Typography.Title
                level={2}
                className="mb-2"
                data-testid="external-task-header"
              >
                My Tasks
              </Typography.Title>
              <Typography.Text
                className="text-gray-600"
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
        <div className="bg-white shadow rounded-lg p-6">
          <ExternalManualTasks />
        </div>
      </div>
    </div>
  );
};
