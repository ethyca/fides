import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  AntButton as Button,
  WarningIcon,
} from "fidesui";
import { ReactNode, useRef } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  message: ReactNode;
  confirmButtonText?: string;
  cancelButtonText?: string;
  handleConfirm: () => void;
}

const WarningModal = ({
  handleConfirm,
  isOpen,
  onClose,
  title,
  message,
  confirmButtonText = "Continue",
  cancelButtonText = "Cancel",
}: Props) => {
  const cancelRef = useRef(null);

  return (
    <AlertDialog
      isOpen={isOpen}
      leastDestructiveRef={cancelRef}
      onClose={onClose}
    >
      <AlertDialogOverlay>
        <AlertDialogContent alignItems="center" textAlign="center">
          <WarningIcon marginTop={3} />
          <AlertDialogHeader fontSize="lg" fontWeight="bold">
            {title}
          </AlertDialogHeader>

          <AlertDialogBody pt={0}>{message}</AlertDialogBody>

          <AlertDialogFooter>
            <Button ref={cancelRef} onClick={onClose} size="large">
              {cancelButtonText}
            </Button>
            <Button
              onClick={() => handleConfirm()}
              type="primary"
              size="large"
              className="ml-3"
              data-testid="warning-modal-confirm-btn"
            >
              {confirmButtonText}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialogOverlay>
    </AlertDialog>
  );
};

export default WarningModal;
