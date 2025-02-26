import {
  AntButtonProps as ButtonProps,
  forwardRef,
  useDisclosure,
} from "fidesui";
import { ReactNode } from "react";

import ApprovePrivacyRequestModal from "~/features/privacy-requests/ApprovePrivacyRequestModal";
import { useMutations } from "~/features/privacy-requests/hooks/useMutations";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

import { StyledButton } from "./StyledButton";

type ApproveButtonProps = {
  buttonProps?: ButtonProps;
  children?: ReactNode;
  onClose?: () => void;
  subjectRequest: PrivacyRequestEntity;
};

const ApproveButton = forwardRef<ApproveButtonProps, "button">(
  ({ buttonProps, children, onClose, subjectRequest }, ref) => {
    const { handleApproveRequest, isLoading } = useMutations({
      subjectRequest,
    });

    const modal = useDisclosure();
    const handleClose = () => {
      modal.onClose();
      onClose?.();
    };

    return (
      <>
        <StyledButton
          ref={ref}
          onClick={modal.onOpen}
          isLoading={isLoading}
          isDisabled={isLoading}
          {...buttonProps}
          data-testid="privacy-request-approve-btn"
        >
          {children}
        </StyledButton>

        <ApprovePrivacyRequestModal
          isOpen={modal.isOpen}
          isLoading={isLoading}
          onClose={handleClose}
          onApproveRequest={handleApproveRequest}
          subjectRequest={subjectRequest}
        />
      </>
    );
  },
);

export default ApproveButton;
