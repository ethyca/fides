import { useGetManualFieldsQuery } from "~/features/datastore-connections/connection-manual-fields.slice";
import { ConnectionType } from "~/types/api";

import { BaseStepHookParams, Step } from "./types";

export const useAddManualTaskStep = ({
  connection,
  connectionOption,
}: BaseStepHookParams): Step | null => {
  // Check if manual tasks/fields have been configured
  const { data: manualFields } = useGetManualFieldsQuery(
    { connectionKey: connection ? connection.key : "" },
    {
      skip: !connection,
    },
  );

  // Only show this step for MANUAL_TASK connection types
  if (connectionOption?.identifier !== ConnectionType.MANUAL_TASK) {
    return null;
  }

  const isComplete = manualFields && manualFields.length > 0;

  return {
    title: "Add a manual task",
    description: isComplete
      ? "Manual tasks have been configured"
      : "Configure manual tasks for this integration. Manual tasks allow you to define custom data collection or processing steps that require human intervention.",
    state: isComplete ? "finish" : "process",
  };
};
