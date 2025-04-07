import { AntButton as Button, AntSpace as Space } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import ConfirmationModal from "../../common/modals/ConfirmationModal";
import { PurposeRestrictionFormModal } from "./PurposeRestrictionFormModal";
import { PurposeRestriction } from "./types";

interface PublisherRestrictionActionCellProps {
  currentValues?: PurposeRestriction;
  existingRestrictions: PurposeRestriction[];
}

export const PublisherRestrictionActionCell = ({
  currentValues,
  existingRestrictions,
}: PublisherRestrictionActionCellProps) => {
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const router = useRouter();

  // Get purpose ID from the URL
  const purposeId = router.query.purpose_id
    ? parseInt(router.query.purpose_id as string, 10)
    : undefined;

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
        existingRestrictions={existingRestrictions}
        purposeId={purposeId}
        restrictionId={currentValues?.id}
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
