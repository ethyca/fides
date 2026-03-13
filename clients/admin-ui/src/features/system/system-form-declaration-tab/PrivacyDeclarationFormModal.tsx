import { Modal } from "fidesui";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";

type DataUseFormModalProps = {
  isOpen: boolean;
  onClose: () => void;
  heading: string;
  isCentered?: boolean;
  testId?: string;
  children: React.ReactNode;
};

export const PrivacyDeclarationFormModal = ({
  isOpen,
  onClose,
  heading,
  isCentered = false,
  testId = "privacy-declaration-modal",
  children,
}: DataUseFormModalProps) => (
  <Modal
    open={isOpen}
    onCancel={onClose}
    centered={isCentered}
    destroyOnClose
    width={MODAL_SIZE.lg}
    data-testid={testId}
    title={heading}
    footer={null}
  >
    {children}
  </Modal>
);
