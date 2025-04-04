import { AntButton as Button, AntSpace as Space } from "fidesui";
import { useState } from "react";

import ConfirmationModal from "../../common/modals/ConfirmationModal";
import { PurposeRestrictionFormModal } from "./PurposeRestrictionFormModal";
import { PurposeRestriction } from "./PurposeRestrictionsTable";

interface PublisherRestrictionActionCellProps {
  currentValues?: PurposeRestriction;
}

export const PublisherRestrictionActionCell = ({
  currentValues,
}: PublisherRestrictionActionCellProps) => {
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);

  const handleDelete = () => {
    // TASK: Delete from API
    console.log("delete");
    setIsDeleteModalOpen(false);
  };

  return (
    <>
      <Space>
        <Button size="small" onClick={() => setIsEditModalOpen(true)}>
          Edit
        </Button>
        <Button size="small" onClick={() => setIsDeleteModalOpen(true)}>
          Delete
        </Button>
      </Space>

      <PurposeRestrictionFormModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        initialValues={currentValues}
      />

      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDelete}
        title="Confirm Deletion"
        message="Are you sure you want to delete this publisher restriction? This action cannot be undone."
        cancelButtonText="Cancel"
        continueButtonText="Delete"
      />
    </>
  );
};
