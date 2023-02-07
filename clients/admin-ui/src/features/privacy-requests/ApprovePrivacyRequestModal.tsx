import ConfirmationModal from "common/ConfirmationModal";
import React, { useCallback } from "react";

type ApproveModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onApproveRequest: () => Promise<any>;
  isLoading: boolean;
};

const ApprovePrivacyRequestModal = ({
  isOpen,
  onClose,
  onApproveRequest,
  isLoading,
}: ApproveModalProps) => {
  const handleSubmit = useCallback(() => {
    onApproveRequest().then(() => {
      onClose();
    });
  }, [onApproveRequest, onClose]);
  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
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
