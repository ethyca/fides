import { Button, Space, useMessage, useModal } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { isErrorResult } from "~/features/common/helpers";

import { PurposeRestrictionFormModal } from "./PurposeRestrictionFormModal";
import { useDeletePublisherRestrictionMutation } from "./tcf-config.slice";
import { PurposeRestriction } from "./types";

interface PublisherRestrictionActionCellProps {
  currentValues?: PurposeRestriction;
  existingRestrictions: PurposeRestriction[];
}

export const PublisherRestrictionActionCell = ({
  currentValues,
  existingRestrictions,
}: PublisherRestrictionActionCellProps) => {
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const router = useRouter();
  const message = useMessage();
  const modal = useModal();

  const [deleteRestriction] = useDeletePublisherRestrictionMutation();

  // Get purpose ID from the URL
  const purposeId = router.query.purpose_id
    ? parseInt(router.query.purpose_id as string, 10)
    : undefined;

  const configurationId = router.query.configuration_id as string;

  const handleDelete = async () => {
    try {
      if (!currentValues?.id) {
        return;
      }
      const result = await deleteRestriction({
        configuration_id: configurationId,
        restriction_id: currentValues.id,
      });
      if (isErrorResult(result)) {
        message.error("Failed to delete publisher restriction");
        return;
      }
      message.success("Publisher restriction deleted successfully");
    } catch (error) {
      message.error("Failed to delete publisher restriction");
    }
  };

  const handleDeleteClick = () => {
    modal.confirm({
      title: "Confirm deletion",
      content:
        "Are you sure you want to delete this publisher restriction? This action cannot be undone.",
      okText: "Delete",
      cancelText: "Cancel",
      centered: true,
      icon: null,
      onOk: handleDelete,
    });
  };

  return (
    <>
      <Space>
        <Button
          size="small"
          onClick={() => setIsEditModalOpen(true)}
          data-testid="edit-restriction-button"
        >
          Edit
        </Button>
        <Button
          size="small"
          onClick={handleDeleteClick}
          data-testid="delete-restriction-button"
        >
          Delete
        </Button>
      </Space>

      <PurposeRestrictionFormModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        initialValues={currentValues}
        existingRestrictions={existingRestrictions}
        purposeId={purposeId}
        restrictionId={currentValues?.id}
        configurationId={configurationId}
      />
    </>
  );
};
