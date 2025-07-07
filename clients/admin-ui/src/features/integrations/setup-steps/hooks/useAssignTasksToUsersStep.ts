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

  // Check if there are actually assigned users, not just if the config exists
  const isComplete = !!(
    manualTaskConfig?.assigned_users &&
    manualTaskConfig.assigned_users.length > 0
  );

  return {
    title: "Assign the tasks to users",
    description: isComplete
      ? "Tasks have been assigned to users"
      : "Assign the configured manual tasks to one or more users.",
    state: isComplete ? "finish" : "process",
  };
};
