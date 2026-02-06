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
import { useState } from "react";

import PolicyConditionForm from "~/features/policies/conditions/PolicyConditionForm";
import { ConditionLeaf } from "~/types/api";

interface PolicyConditionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConditionSaved: (condition: ConditionLeaf) => Promise<void>;
  editingCondition?: ConditionLeaf | null;
  policyKey: string;
}

const PolicyConditionModal = ({
  isOpen,
  onClose,
  onConditionSaved,
  editingCondition,
  policyKey,
}: PolicyConditionModalProps) => {
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditing = !!editingCondition;

  const handleSubmit = async (condition: ConditionLeaf) => {
    try {
      setIsSubmitting(true);
      await onConditionSaved(condition);
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
    <Modal
      isCentered
      isOpen={isOpen}
      size="lg"
      onClose={onClose}
      data-testid="policy-condition-modal"
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
                ? "Update the condition settings for this policy."
                : "Configure a new condition that determines when this policy applies. Select a field from the privacy request to create the condition."}
            </Box>
            <PolicyConditionForm
              onAdd={handleSubmit}
              onCancel={handleCancel}
              editingCondition={editingCondition}
              isSubmitting={isSubmitting}
              policyKey={policyKey}
            />
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default PolicyConditionModal;
