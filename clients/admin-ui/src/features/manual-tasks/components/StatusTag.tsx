import { Tag as AntTag } from "fidesui";

import { TaskStatus } from "~/types/api/models/ManualTask";

interface Props {
  status: TaskStatus;
}

const statusColors: Record<TaskStatus, string> = {
  new: "blue",
  completed: "green",
  skipped: "orange",
};

const statusLabels: Record<TaskStatus, string> = {
  new: "New",
  completed: "Completed",
  skipped: "Skipped",
};

export const StatusTag = ({ status }: Props) => (
  <AntTag color={statusColors[status]}>{statusLabels[status]}</AntTag>
);
