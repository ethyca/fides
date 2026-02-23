import { Modal, Typography } from "fidesui";
import { useState } from "react";

import type { ConditionLeaf } from "~/types/api";

import { PolicyConditionForm } from "./PolicyConditionForm";

interface AddEditPolicyConditionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConditionSaved: (condition: ConditionLeaf) => Promise<void>;
  editingCondition?: ConditionLeaf | null;
}

export const AddEditPolicyConditionModal = ({
  isOpen,
  onClose,
  onConditionSaved,
  editingCondition,
}: AddEditPolicyConditionModalProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isEditing = !!editingCondition;

  const handleSubmit = async (condition: ConditionLeaf) => {
    try {
      setIsSubmitting(true);
      await onConditionSaved(condition);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      title={isEditing ? "Edit condition" : "Add condition"}
      footer={null}
      destroyOnClose
      width={600}
      data-testid="add-edit-condition-modal"
    >
      <Typography.Paragraph type="secondary">
        {isEditing
          ? "Update the condition for this policy."
          : "Add a location-based condition to control when this policy applies."}
      </Typography.Paragraph>
      <PolicyConditionForm
        onSubmit={handleSubmit}
        onCancel={onClose}
        editingCondition={editingCondition}
        isSubmitting={isSubmitting}
      />
    </Modal>
  );
};
