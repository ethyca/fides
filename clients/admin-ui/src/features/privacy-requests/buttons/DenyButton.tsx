import {
  AntButtonProps as ButtonProps,
  forwardRef,
  useDisclosure,
} from "fidesui";
import { ReactNode } from "react";

import DenyPrivacyRequestModal from "~/features/privacy-requests/DenyPrivacyRequestModal";
import { useMutations } from "~/features/privacy-requests/hooks/useMutations";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

import { StyledButton } from "./StyledButton";

type DenyButtonProps = {
  buttonProps?: ButtonProps;
  children?: ReactNode;
  onClose?: () => void;
  subjectRequest: PrivacyRequestEntity;
};

const DenyButton = forwardRef<DenyButtonProps, "button">(
  ({ buttonProps, children, onClose, subjectRequest }, ref) => {
    const { handleDenyRequest, isLoading } = useMutations({ subjectRequest });

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
          data-testid="privacy-request-deny-btn"
        >
          {children}
        </StyledButton>

        <DenyPrivacyRequestModal
          isOpen={modal.isOpen}
          onClose={handleClose}
          onDenyRequest={handleDenyRequest}
        />
      </>
    );
  },
);

export default DenyButton;
