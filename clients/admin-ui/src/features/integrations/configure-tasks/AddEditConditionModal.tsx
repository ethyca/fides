import {
  AntMessage as message,
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

import { ConditionLeaf } from "~/types/api";

import AddConditionForm from "./AddConditionForm";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onConditionSaved: (condition: ConditionLeaf) => Promise<void>;
  editingCondition?: ConditionLeaf | null;
};

const AddEditConditionModal = ({
  isOpen,
  onClose,
  onConditionSaved,
  editingCondition,
}: Props) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditing = !!editingCondition;

  const handleSubmit = async (condition: ConditionLeaf) => {
    try {
      setIsSubmitting(true);
      await onConditionSaved(condition);
      onClose(); // Only close if save was successful
    } catch (error: any) {
      // Parse API error message
      let errorMessage = "Failed to save condition. Please try again.";

      if (error?.data?.detail) {
        // Handle API validation errors like the example:
        // "Found 1 validation error(s):\n\nField: asdasd.d\n  - Invalid field address format: asdasd.d, expected format: dataset_key:collection:field.nested_field\n"
        const detail = error.data.detail;

        if (detail.includes("validation error")) {
          // Extract the field-specific error message
          const lines = detail.split("\n");
          const errorLine = lines.find((line) => line.trim().startsWith("- "));
          if (errorLine) {
            errorMessage = errorLine.trim().replace(/^\s*-\s*/, "");
          } else {
            // Fallback: just use the detail as-is, cleaned up
            errorMessage = detail
              .replace(/Found \d+ validation error\(s\):\s*\n*/i, "")
              .trim();
          }
        } else {
          // For non-validation errors, use the detail directly
          errorMessage = detail;
        }
      } else if (error?.message) {
        // Handle client-side errors (like duplicate condition check)
        errorMessage = error.message;
      }

      message.error(errorMessage);
      // Don't close modal on error - let user fix the issue
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
                : "Configure a new condition that must be met before a task is created. Use dot notation for nested field paths (e.g., user.age, custom_fields.country)."}
            </Box>
            <AddConditionForm
              onAdd={handleSubmit}
              onCancel={handleCancel}
              editingCondition={editingCondition}
              isSubmitting={isSubmitting}
            />
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default AddEditConditionModal;
