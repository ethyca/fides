import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  Button,
} from "@fidesui/react";
import { ReactNode, useRef } from "react";

import { WarningIcon } from "./Icon";

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
            <Button
              data-testid="warning-modal-confirm-btn"
              onClick={() => handleConfirm()}
              variant="outline"
            >
              {confirmButtonText}
            </Button>
            <Button
              colorScheme="primary"
              ref={cancelRef}
              onClick={onClose}
              ml={3}
            >
              {cancelButtonText}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialogOverlay>
    </AlertDialog>
  );
};

export default WarningModal;
