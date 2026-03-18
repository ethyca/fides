import {
  ChakraBox as Box,
  ChakraVStack as VStack,
  Modal,
  useMessage,
} from "fidesui";
import React, { useState } from "react";

import {
  isErrorWithDetail,
  isErrorWithDetailArray,
} from "~/features/common/helpers";
import {
  useCreateManualFieldMutation,
  useUpdateManualFieldMutation,
} from "~/features/datastore-connections/connection-manual-fields.slice";
import {
  ConnectionConfigurationResponse,
  ManualFieldCreate,
  ManualFieldUpdate,
} from "~/types/api";

import AddManualTaskForm from "./AddManualTaskForm";
import { Task } from "./types";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  integration: ConnectionConfigurationResponse;
  onTaskAdded: () => void;
  editingTask?: Task | null;
};

const AddManualTaskModal = ({
  isOpen,
  onClose,
  integration,
  onTaskAdded,
  editingTask,
}: Props) => {
  const message = useMessage();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [createManualField] = useCreateManualFieldMutation();
  const [updateManualField] = useUpdateManualFieldMutation();

  const isEditing = !!editingTask;

  const handleSubmit = async (values: any) => {
    try {
      setIsSubmitting(true);

      if (isEditing && editingTask) {
        // Update existing field
        const updatedField: ManualFieldUpdate = {
          label: values.name,
          help_text: values.description,
          field_type: values.fieldType,
          request_type: values.requestType,
        };

        await updateManualField({
          connectionKey: integration.key as string,
          manualFieldId: editingTask.id,
          body: updatedField,
        }).unwrap();

        message.success("Manual task updated successfully!");
      } else {
        // Create new field
        const newField: ManualFieldCreate = {
          key: values.key || undefined,
          label: values.name,
          help_text: values.description,
          field_type: values.fieldType,
          request_type: values.requestType,
        };

        await createManualField({
          connectionKey: integration.key as string,
          body: newField,
        }).unwrap();

        message.success("Manual task added successfully!");
      }

      onTaskAdded();
      onClose();
    } catch (error: any) {
      let errorMsg = "An unexpected error occurred. Please try again.";
      if (isErrorWithDetail(error)) {
        errorMsg = error.data.detail;
      } else if (isErrorWithDetailArray(error)) {
        errorMsg = error.data.detail[0].msg;
      }
      message.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    onClose();
  };

  return (
    <Modal
      centered
      open={isOpen}
      onCancel={onClose}
      destroyOnHidden
      wrapProps={{ "data-testid": "add-manual-task-modal" }}
      styles={{ body: { minWidth: "775px" } }}
      title={isEditing ? "Edit manual task" : "Add manual task"}
      footer={null}
    >
      <VStack align="stretch" gap="16px">
        <Box color="gray.700" fontSize="14px">
          {isEditing
            ? "Update the manual task configuration for this integration."
            : "Configure a new manual task for this integration. Define the task name, description, and any specific parameters needed for execution."}
        </Box>
        <AddManualTaskForm
          isSubmitting={isSubmitting}
          onSaveClick={handleSubmit}
          onCancel={handleCancel}
          editingTask={editingTask}
        />
      </VStack>
    </Modal>
  );
};

export default AddManualTaskModal;
