import { BadgeCell } from "~/features/common/table/v2";
import { TaskStatus } from "~/types/api/models/ManualTask";

interface Props {
  status: TaskStatus;
}

const statusProps: Record<TaskStatus, { colorScheme: string; label: string }> =
  {
    new: {
      colorScheme: "info",
      label: "New",
    },
    completed: {
      colorScheme: "success",
      label: "Completed",
    },
    skipped: {
      colorScheme: "warning",
      label: "Skipped",
    },
  };

export const StatusTag = ({ status }: Props) => (
  <BadgeCell
    color={statusProps[status].colorScheme}
    value={statusProps[status].label}
    data-testid="manual-task-status-badge"
  />
);
