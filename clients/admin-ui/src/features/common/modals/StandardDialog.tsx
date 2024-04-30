import {
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  ModalProps,
  ThemingProps,
} from "@fidesui/react";

export interface StandardDialogProps extends ModalProps {
  heading?: string;
  cancelButtonText?: string;
  cancelButtonThemingProps?: ThemingProps<"Button">;
  continueButtonText?: string;
  continueButtonThemingProps?: ThemingProps<"Button">;
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
  cancelButtonThemingProps,
  continueButtonText,
  continueButtonThemingProps,
  "data-testid": testId = "standard-dialog",
  ...props
}: StandardDialogProps): JSX.Element => {
  const { onClose } = props;
  return (
    <Modal {...props}>
      <ModalOverlay />
      <ModalContent>
        {heading && <ModalHeader>{heading}</ModalHeader>}
        <ModalCloseButton />
        {children && <ModalBody>{children}</ModalBody>}
        <ModalFooter
          gap={3}
          width="100%"
          sx={{ "& button": { width: "100%" } }}
        >
          <Button
            variant="outline"
            onClick={() => {
              if (onCancel) {
                onCancel();
              }
              onClose();
            }}
            data-testid={`${testId ? `${testId}-` : ""}cancel-btn`}
            isDisabled={isLoading}
            {...cancelButtonThemingProps}
          >
            {cancelButtonText || "Cancel"}
          </Button>
          <Button
            colorScheme="primary"
            onClick={onConfirm}
            data-testid={`${testId ? `${testId}-` : ""}cancel-btn`}
            isLoading={isLoading}
            {...cancelButtonThemingProps}
          >
            {continueButtonText || "Continue"}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default StandardDialog;
