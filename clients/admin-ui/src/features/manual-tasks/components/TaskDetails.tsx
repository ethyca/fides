import { AntTag as Tag, AntTypography as Typography } from "fidesui";

import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import {
  ActionType,
  ManualFieldListItem,
  ManualFieldRequestType,
} from "~/types/api";

interface TaskDetailsProps {
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

export const TaskDetails = ({ task }: TaskDetailsProps) => {
  // Map the request type using the existing map
  const actionType =
    task.request_type === ManualFieldRequestType.ACCESS
      ? ActionType.ACCESS
      : ActionType.ERASURE;
  const requestTypeDisplay =
    SubjectRequestActionTypeMap.get(actionType) || task.request_type;

  return (
    <div
      className="flex flex-col space-y-3"
      data-testid="task-details-container"
    >
      <TaskInfoRow label="Name">
        <Typography.Text>{task.name}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Description">
        <Typography.Text>{task.description || "-"}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Request Type">
        <Typography.Text>{requestTypeDisplay}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Assigned To">
        {task.assigned_users && task.assigned_users.length > 0 ? (
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
      {task.privacy_request.subject_identities &&
      Object.keys(task.privacy_request.subject_identities).length > 0 ? (
        <TaskInfoRow label="Subject identities">
          <div className="flex flex-wrap gap-1">
            {Object.entries(
              task.privacy_request.subject_identities as Record<string, string>,
            ).map(([key, value]) => (
              <Tag key={key}>
                {key}: {String(value)}
              </Tag>
            ))}
          </div>
        </TaskInfoRow>
      ) : null}

      {/* Show custom fields if available */}
      {task.privacy_request.custom_fields &&
      Object.keys(task.privacy_request.custom_fields).length > 0 ? (
        <TaskInfoRow label="Custom fields">
          <div className="flex flex-wrap gap-1">
            {Object.entries(task.privacy_request.custom_fields)
              .filter(([, value]) => value) // Only show fields with values
              .map(([key, value]) => (
                <Tag key={key}>
                  {key}: {String(value)}
                </Tag>
              ))}
          </div>
        </TaskInfoRow>
      ) : null}
    </div>
  );
};
