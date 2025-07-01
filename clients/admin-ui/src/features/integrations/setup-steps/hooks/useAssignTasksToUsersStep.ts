import { useGetManualTaskConfigQuery } from "~/features/datastore-connections/connection-manual-tasks.slice";
import { ConnectionType } from "~/types/api";

import { BaseStepHookParams, Step } from "./types";

export const useAssignTasksToUsersStep = ({
  connection,
  connectionOption,
}: BaseStepHookParams): Step | null => {
  // Check if users have been assigned to manual tasks
  const { data: manualTaskConfig } = useGetManualTaskConfigQuery(
    { connectionKey: connection ? connection.key : "" },
    {
      skip: !connection,
    },
  );

  // Only show this step for MANUAL_TASK connection types
  if (connectionOption?.identifier !== ConnectionType.MANUAL_TASK) {
    return null;
  }

  // For now, we'll assume this step is complete if the connection exists and manual task config exists
  // In the future, we could check if there are specific users assigned
  const isComplete = !!manualTaskConfig;

  return {
    title: "Assign the tasks to users",
    description: isComplete
      ? "Tasks have been assigned to users"
      : "Assign the configured manual tasks to specific users who will be responsible for completing them during privacy requests.",
    state: isComplete ? "finish" : "process",
  };
};
