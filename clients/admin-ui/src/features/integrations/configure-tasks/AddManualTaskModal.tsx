import { useAlert, useAPIHelper } from "common/hooks";
import {
  useCreateAccessManualWebhookMutation,
  useGetAccessManualHookQuery,
  usePatchAccessManualWebhookMutation,
} from "datastore-connections/datastore-connection.slice";
import {
  CreateAccessManualWebhookRequest,
  PatchAccessManualWebhookRequest,
} from "datastore-connections/types";
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

import { ConnectionConfigurationResponse } from "~/types/api";

import AddManualTaskForm from "./AddManualTaskForm";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  integration: ConnectionConfigurationResponse;
  onTaskAdded: () => void;
};

const AddManualTaskModal = ({
  isOpen,
  onClose,
  integration,
  onTaskAdded,
}: Props) => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: existingData } = useGetAccessManualHookQuery(
    integration ? integration.key : "",
    {
      skip: !integration,
    },
  );

  const [createAccessManualWebhook] = useCreateAccessManualWebhookMutation();
  const [patchAccessManualWebhook] = usePatchAccessManualWebhookMutation();

  const handleSubmit = async (values: any) => {
    try {
      setIsSubmitting(true);

      // Check if we have existing fields
      const existingFields = existingData?.fields || [];
      const hasExistingFields = existingFields.length > 0;

      // Create the new field object
      const newField = {
        pii_field: values.name,
        types: values.types || [],
        dsr_package_label: values.description,
        data_categories: values.data_categories || [],
        assignedTo: values.assignedTo || [],
      };

      if (hasExistingFields) {
        // Use PATCH - include all existing fields plus the new one
        const params: PatchAccessManualWebhookRequest = {
          connection_key: integration.key as string,
          body: {
            fields: [...existingFields, newField],
          },
        };
        await patchAccessManualWebhook(params).unwrap();
      } else {
        // Use POST - first time adding fields
        const params: CreateAccessManualWebhookRequest = {
          connection_key: integration.key as string,
          body: {
            fields: [newField],
          },
        };
        await createAccessManualWebhook(params).unwrap();
      }

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
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default AddManualTaskModal;
