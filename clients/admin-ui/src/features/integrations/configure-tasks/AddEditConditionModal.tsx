import { useAPIHelper } from "common/hooks";
import {
  ChakraBox as Box,
  ChakraModal as Modal,
  ChakraModalBody as ModalBody,
  ChakraModalCloseButton as ModalCloseButton,
  ChakraModalContent as ModalContent,
  ChakraModalHeader as ModalHeader,
  ChakraModalOverlay as ModalOverlay,
  ChakraVStack as VStack,
} from "fidesui";
import React, { useState } from "react";

import { ConditionLeaf } from "~/types/api";

import AddConditionForm from "./AddConditionForm";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onConditionSaved: (condition: ConditionLeaf) => Promise<void>;
  editingCondition?: ConditionLeaf | null;
  connectionKey: string;
};

const AddEditConditionModal = ({
  isOpen,
  onClose,
  onConditionSaved,
  editingCondition,
  connectionKey,
}: Props) => {
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditing = !!editingCondition;

  const handleSubmit = async (condition: ConditionLeaf) => {
    try {
      setIsSubmitting(true);
      await onConditionSaved(condition);
      onClose(); // Only close if save was successful
    } catch (error) {
      handleError(error);
      // Don't close modal on error - let user fix the issue
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    onClose();
  };

  return (
    <Modal
      isCentered
      isOpen={isOpen}
      size="lg"
      onClose={onClose}
      data-testid="add-edit-condition-modal"
    >
      <ModalOverlay />
      <ModalContent minWidth="650px">
        <ModalHeader>
          {isEditing ? "Edit condition" : "Add condition"}
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack align="stretch" gap="16px">
            <Box color="gray.700" fontSize="14px">
              {isEditing
                ? "Update the condition settings for task creation."
                : "Configure a new condition that must be met before a task is created. Select a field from your datasets or from the privacy request to create the condition."}
            </Box>
            <AddConditionForm
              onAdd={handleSubmit}
              onCancel={handleCancel}
              editingCondition={editingCondition}
              isSubmitting={isSubmitting}
              connectionKey={connectionKey}
            />
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default AddEditConditionModal;
