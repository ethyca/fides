/**
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/manual-tasks/components/TaskDetails.tsx
 *
 * Key differences for external users:
 * - Simplified styling for external interface
 * - Uses external data-testids for Cypress testing
 * - No complex routing/navigation features
 *
 * IMPORTANT: When updating admin-ui TaskDetails.tsx, review this component for sync!
 */

import {
  AntFlex as Flex,
  AntTag as Tag,
  AntTypography as Typography,
} from "fidesui";

import { ManualFieldListItem } from "../external-manual-tasks.slice";

interface ExternalTaskDetailsProps {
  task: ManualFieldListItem;
}

// Helper component for displaying task information rows
const TaskInfoRow = ({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) => (
  <Flex align="center" gap="small">
    <div
      style={{
        flexShrink: 0,
        flexGrow: 0,
        flexBasis: "33%",
        paddingRight: "8px",
      }}
    >
      <Typography.Text style={{ color: "#374151" }}>{label}:</Typography.Text>
    </div>
    <div style={{ minWidth: 0, flexShrink: 1, flexGrow: 1, color: "#6b7280" }}>
      {children}
    </div>
  </Flex>
);

export const ExternalTaskDetails = ({ task }: ExternalTaskDetailsProps) => {
  // Capitalize request type for display
  const requestTypeDisplay =
    task.privacy_request.request_type.charAt(0).toUpperCase() +
    task.privacy_request.request_type.slice(1);

  return (
    <Flex vertical gap="middle" data-testid="task-details-container">
      <TaskInfoRow label="Name">
        <Typography.Text data-testid="task-details-name">
          {task.name}
        </Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Description">
        <Typography.Text>
          {task.description || "No description"}
        </Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Request Type">
        <Typography.Text>{requestTypeDisplay}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="System">
        <Typography.Text>{task.system?.name || "No system"}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Assigned To">
        {task.assigned_users && task.assigned_users.length > 0 ? (
          <Flex wrap="wrap" gap="small" data-testid="assigned-users-tags">
            {task.assigned_users.map((user) => (
              <Tag key={user.id} data-testid={`assigned-user-tag-${user.id}`}>
                {`${user.first_name || ""} ${user.last_name || ""}`.trim() ||
                  user.email_address ||
                  "Unknown User"}
              </Tag>
            ))}
          </Flex>
        ) : (
          <Typography.Text>No one assigned</Typography.Text>
        )}
      </TaskInfoRow>

      {/* Show all available identity fields */}
      {task.privacy_request.subject_identities &&
      Object.keys(task.privacy_request.subject_identities).length > 0 ? (
        <TaskInfoRow label="Subject identities">
          <Flex wrap="wrap" gap="small">
            {Object.entries(task.privacy_request.subject_identities).map(
              ([key, value]) => (
                <Tag key={key}>
                  {key}: {value}
                </Tag>
              ),
            )}
          </Flex>
        </TaskInfoRow>
      ) : null}

      {/* Show custom fields if available */}
      {task.privacy_request.custom_fields &&
      task.privacy_request.custom_fields.length > 0 ? (
        <TaskInfoRow label="Custom fields">
          <Flex wrap="wrap" gap="small">
            {task.privacy_request.custom_fields
              .filter((field) => field.value) // Only show fields with values
              .map((field) => (
                <Tag key={field.label}>
                  {field.label}: {field.value}
                </Tag>
              ))}
          </Flex>
        </TaskInfoRow>
      ) : null}
    </Flex>
  );
};
