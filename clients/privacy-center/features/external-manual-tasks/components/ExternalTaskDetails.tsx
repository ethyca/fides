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

import { AntTag as Tag, AntTypography as Typography } from "fidesui";

import {
  IdentityField,
  ManualFieldListItem,
} from "../external-manual-tasks.slice";

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
  <div className="flex items-center">
    <div className="shrink-0 grow-0 basis-1/3 pr-2">
      <Typography.Text className="text-gray-700">{label}:</Typography.Text>
    </div>
    <div className="min-w-0 shrink grow text-gray-600">{children}</div>
  </div>
);

export const ExternalTaskDetails = ({ task }: ExternalTaskDetailsProps) => {
  // Capitalize request type for display
  const requestTypeDisplay =
    task.privacy_request.request_type.charAt(0).toUpperCase() +
    task.privacy_request.request_type.slice(1);

  return (
    <div className="flex flex-col space-y-3">
      <TaskInfoRow label="Name">
        <Typography.Text data-testid="task-details-name">
          {task.name}
        </Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Description">
        <Typography.Text>{task.description}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Request Type">
        <Typography.Text>{requestTypeDisplay}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="System">
        <Typography.Text>{task.system.name}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Assigned To">
        {task.assigned_users.length > 0 ? (
          <div
            className="flex flex-wrap gap-1"
            data-testid="assigned-users-tags"
          >
            {task.assigned_users.map((user) => (
              <Tag key={user.id} data-testid={`assigned-user-tag-${user.id}`}>
                {`${user.first_name || ""} ${user.last_name || ""}`.trim() ||
                  user.email_address ||
                  "Unknown User"}
              </Tag>
            ))}
          </div>
        ) : (
          <Typography.Text>No one assigned</Typography.Text>
        )}
      </TaskInfoRow>

      {/* Show all available identity fields */}
      {task.privacy_request.subject_identity &&
        Object.entries(task.privacy_request.subject_identity).map(
          ([key, identity]) => (
            <TaskInfoRow key={key} label={`Identity - ${identity.label}`}>
              <Typography.Text>{identity.value}</Typography.Text>
            </TaskInfoRow>
          ),
        )}
    </div>
  );
};
