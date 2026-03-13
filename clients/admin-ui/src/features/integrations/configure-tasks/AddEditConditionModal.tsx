import { useAPIHelper } from "common/hooks";
import { Modal, Typography } from "fidesui";
import React, { useState } from "react";

import { ConditionLeaf } from "~/types/api";

import AddConditionForm from "./AddConditionForm";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onConditionSaved: (condition: ConditionLeaf) => Promise<void>;
  editingCondition?: ConditionLeaf | null;
  connectionKey: string;
  /**
   * When true, hides the dataset field source option and filters privacy request
   * fields to only those available for consent requests.
   */
  isConsentOnly?: boolean;
};

const getModalDescription = (
  isEditing: boolean,
  isConsentOnly: boolean,
): string => {
  if (isEditing) {
    return "Update the condition settings for task creation.";
  }
  if (isConsentOnly) {
    return "Configure a new condition that must be met before a task is created. Select a privacy request field to create the condition.";
  }
  return "Configure a new condition that must be met before a task is created. Select a field from your datasets or from the privacy request to create the condition.";
};

const AddEditConditionModal = ({
  isOpen,
  onClose,
  onConditionSaved,
  editingCondition,
  connectionKey,
  isConsentOnly = false,
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
      centered
      open={isOpen}
      onCancel={onClose}
      destroyOnHidden
      data-testid="add-edit-condition-modal"
      styles={{ body: { minWidth: "650px" } }}
      title={isEditing ? "Edit condition" : "Add condition"}
      footer={null}
    >
      <Typography.Paragraph>
        {getModalDescription(isEditing, isConsentOnly)}
      </Typography.Paragraph>
      <AddConditionForm
        onAdd={handleSubmit}
        onCancel={handleCancel}
        editingCondition={editingCondition}
        isSubmitting={isSubmitting}
        connectionKey={connectionKey}
        isConsentOnly={isConsentOnly}
      />
    </Modal>
  );
};

export default AddEditConditionModal;
