import { Modal } from "fidesui";
import React from "react";

import useConfirmDirtyClose from "~/features/common/hooks/useConfirmDirtyClose";

type ModalProps = React.ComponentProps<typeof Modal>;

interface ConfirmCloseModalProps extends Omit<ModalProps, "onCancel"> {
  /**
   * Called when the modal should close — either immediately (when clean)
   * or after the user confirms (when dirty).
   */
  onClose: () => void;
  /**
   * Evaluated at event time to check whether the form has unsaved changes.
   * Use `() => formik.dirty` for Formik forms or `() => form.isFieldsTouched()`
   * for AntD forms.
   */
  getIsDirty: () => boolean;
}

/**
 * A Modal wrapper that guards against accidental dismissal of dirty forms.
 *
 * When `getIsDirty()` returns true, pressing Escape or clicking the overlay
 * shows a confirmation dialog instead of closing immediately.
 *
 * Use this instead of `<Modal>` for any modal that contains a form.
 */
const ConfirmCloseModal = ({
  onClose,
  getIsDirty,
  children,
  ...modalProps
}: ConfirmCloseModalProps) => {
  const handleCancel = useConfirmDirtyClose(onClose, getIsDirty);

  return (
    <Modal {...modalProps} onCancel={handleCancel}>
      {children}
    </Modal>
  );
};

export default ConfirmCloseModal;
