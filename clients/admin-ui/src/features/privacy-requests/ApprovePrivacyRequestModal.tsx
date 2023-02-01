import ConfirmationModal from "common/ConfirmationModal";
import React, { useCallback } from "react";

type ApproveModalProps = {
  isOpen: boolean;
  handleMenuClose: () => void;
  handleApproveRequest: () => Promise<any>;
  isLoading: boolean;
};

const ApprovePrivacyRequestModal = ({
  isOpen,
  handleMenuClose,
  handleApproveRequest,
  isLoading,
}: ApproveModalProps) => {
  const handleSubmit = useCallback(() => {
    handleApproveRequest().then(() => {
      handleMenuClose();
    });
  }, [handleApproveRequest, handleMenuClose]);
  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={handleMenuClose}
      onConfirm={handleSubmit}
      message="Are you sure you want to approve this privacy request?"
      continueButtonText="Confirm"
      continueButtonThemingProps={{
        variant: "solid",
      }}
      isLoading={isLoading}
      returnFocusOnClose={false}
      isCentered
    />
  );
};

export default ApprovePrivacyRequestModal;
