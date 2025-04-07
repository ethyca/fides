import { AntButton as Button, AntSpace as Space, useToast } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import ConfirmationModal from "../../common/modals/ConfirmationModal";
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
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const router = useRouter();
  const toast = useToast();

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
        toast(errorToastParams("Failed to delete publisher restriction"));
        return;
      }
      setIsDeleteModalOpen(false);
      toast(successToastParams("Publisher restriction deleted successfully"));
    } catch (error) {
      toast(errorToastParams("Failed to delete publisher restriction"));
    }
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
        configurationId={configurationId}
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
