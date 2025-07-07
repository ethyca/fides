import { useAlert, useAPIHelper } from "common/hooks";
import {
  Box,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  VStack,
} from "fidesui";
import React, { useState } from "react";

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
import { Task } from "./useTaskColumns";

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
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
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

        successAlert("Manual task updated successfully!");
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

        successAlert("Manual task added successfully!");
      }

      onTaskAdded();
      onClose();
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    onClose();
  };

  return (
    <Modal isCentered isOpen={isOpen} size="lg" onClose={onClose}>
      <ModalOverlay />
      <ModalContent minWidth="775px">
        <ModalHeader>
          {isEditing ? "Edit manual task" : "Add manual task"}
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
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
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default AddManualTaskModal;
