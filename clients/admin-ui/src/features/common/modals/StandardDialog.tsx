import {
  AntButton as Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  ModalProps,
} from "fidesui";

export interface StandardDialogProps extends ModalProps {
  heading?: string;
  cancelButtonText?: string;
  continueButtonText?: string;
  onCancel?: () => void;
  onConfirm: () => void;
  isLoading?: boolean;
  "data-testid"?: string;
}

const StandardDialog = ({
  children,
  heading,
  onCancel,
  onConfirm,
  isLoading,
  cancelButtonText,
  continueButtonText,
  "data-testid": testId = "standard-dialog",
  ...props
}: StandardDialogProps): JSX.Element => {
  const { onClose } = props;
  return (
    <Modal closeOnOverlayClick={isLoading} {...props}>
      <ModalOverlay />
      <ModalContent data-testid={testId}>
        {heading && <ModalHeader>{heading}</ModalHeader>}
        <ModalCloseButton isDisabled={isLoading} />
        {children && <ModalBody>{children}</ModalBody>}
        <ModalFooter
          gap={3}
          width="100%"
          sx={{ "& button": { width: "100%" } }}
        >
          <Button
            onClick={() => {
              if (onCancel) {
                onCancel();
              }
              onClose();
            }}
            data-testid={`${testId ? `${testId}-` : ""}cancel-btn`}
            disabled={isLoading}
          >
            {cancelButtonText || "Cancel"}
          </Button>
          <Button
            onClick={onConfirm}
            type="primary"
            data-testid={`${testId ? `${testId}-` : ""}continue-btn`}
            loading={isLoading}
          >
            {continueButtonText || "Continue"}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default StandardDialog;
