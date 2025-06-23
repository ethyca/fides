import { AntTypography as Typography } from "fidesui";

import { ManualTask } from "../mocked/types";

interface TaskDetailsProps {
  task: ManualTask;
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
  return (
    <div className="flex flex-col space-y-3">
      <TaskInfoRow label="Name">
        <Typography.Text>{task.name}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Description">
        <Typography.Text>{task.description}</Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Request Type">
        <Typography.Text>
          {task.privacy_request.request_type.charAt(0).toUpperCase() +
            task.privacy_request.request_type.slice(1)}
        </Typography.Text>
      </TaskInfoRow>

      <TaskInfoRow label="Assigned To">
        {task.assigned_users.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {task.assigned_users.map((user) => (
              <span
                key={user.id}
                className="inline-flex items-center rounded bg-gray-100 px-2 py-1 text-xs text-gray-800"
              >
                {`${user.first_name || ""} ${user.last_name || ""}`.trim() ||
                  user.email_address ||
                  "Unknown User"}
              </span>
            ))}
          </div>
        ) : (
          <Typography.Text>No one assigned</Typography.Text>
        )}
      </TaskInfoRow>
    </div>
  );
};
