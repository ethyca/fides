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

import { useCreateManualFieldMutation } from "~/features/datastore-connections/connection-manual-fields.slice";
import {
  ConnectionConfigurationResponse,
  ManualFieldCreate,
} from "~/types/api";

import AddManualTaskForm from "./AddManualTaskForm";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  integration: ConnectionConfigurationResponse;
  onTaskAdded: () => void;
  selectedUsers: string[];
};

const AddManualTaskModal = ({
  isOpen,
  onClose,
  integration,
  onTaskAdded,
  selectedUsers,
}: Props) => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [createManualField] = useCreateManualFieldMutation();

  const handleSubmit = async (values: any) => {
    try {
      setIsSubmitting(true);

      // Create the new manual field
      const newField: ManualFieldCreate = {
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
        <ModalHeader>Add Manual Task</ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack align="stretch" gap="16px">
            <Box color="gray.700" fontSize="14px">
              Configure a new manual task for this integration. Define the task
              name, description, and any specific parameters needed for
              execution.
            </Box>
            <AddManualTaskForm
              isSubmitting={isSubmitting}
              onSaveClick={handleSubmit}
              onCancel={handleCancel}
            />
            <Box mt={4} p={3} bg="gray.50" borderRadius="md">
              <Box color="gray.600" fontSize="sm">
                <strong>Note:</strong> Task assignment is configured above the
                table. Selected users:{" "}
                {selectedUsers.length > 0
                  ? selectedUsers.join(", ")
                  : "None selected"}
              </Box>
            </Box>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default AddManualTaskModal;
