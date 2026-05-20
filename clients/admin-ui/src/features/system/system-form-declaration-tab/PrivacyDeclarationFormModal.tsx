import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";

type DataUseFormModalProps = {
  isOpen: boolean;
  onClose: () => void;
  heading: string;
  isCentered?: boolean;
  testId?: string;
  children: React.ReactNode;
  /** Evaluated at event time to guard against accidental close of a dirty form. */
  getIsDirty: () => boolean;
};

export const PrivacyDeclarationFormModal = ({
  isOpen,
  onClose,
  heading,
  isCentered = false,
  testId = "privacy-declaration-modal",
  children,
  getIsDirty,
}: DataUseFormModalProps) => (
  <ConfirmCloseModal
    open={isOpen}
    onClose={onClose}
    getIsDirty={getIsDirty}
    centered={isCentered}
    destroyOnHidden
    width={MODAL_SIZE.lg}
    data-testid={testId}
    title={heading}
    footer={null}
  >
    {children}
  </ConfirmCloseModal>
);
