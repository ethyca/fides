import { AntMessage as message } from "fidesui";
import { useCallback, useEffect, useState } from "react";

import {
  useDeleteManualFieldMutation,
  useGetManualFieldsQuery,
} from "~/features/datastore-connections/connection-manual-fields.slice";
import {
  ConnectionConfigurationResponse,
  ManualFieldResponse,
} from "~/types/api";

import { Task } from "../types";

interface UseManualTaskManagementProps {
  integration: ConnectionConfigurationResponse;
}

export const useManualTaskManagement = ({
  integration,
}: UseManualTaskManagementProps) => {
  const [manualTasks, setManualTasks] = useState<Task[]>([]);

  const { data, refetch } = useGetManualFieldsQuery(
    { connectionKey: integration ? integration.key : "" },
    {
      skip: !integration,
    },
  );

  const [deleteManualField] = useDeleteManualFieldMutation();

  // Transform manual fields data into task format
  useEffect(() => {
    if (data) {
      const transformedTasks = data.map((field: ManualFieldResponse) => ({
        id: field.id,
        name: field.label,
        description: field.help_text,
        fieldType: field.field_type,
        requestType: field.request_type,
        originalField: field,
      }));
      setManualTasks(transformedTasks);
    }
  }, [data]);

  const deleteManualTask = useCallback(
    async (task: Task) => {
      try {
        await deleteManualField({
          connectionKey: integration.key as string,
          manualFieldId: task.id,
        }).unwrap();

        refetch();
      } catch (error) {
        message.error("Failed to delete manual task. Please try again.");
      }
    },
    [deleteManualField, integration.key, refetch],
  );

  const refreshManualTasks = useCallback(() => {
    refetch();
  }, [refetch]);

  return {
    manualTasks,
    deleteManualTask,
    refreshManualTasks,
    isLoading: !data,
  };
};
