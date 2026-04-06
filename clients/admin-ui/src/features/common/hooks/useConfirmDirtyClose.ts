import { useModal } from "fidesui";
import { useEffect, useRef } from "react";

/**
 * Returns a close handler that shows a confirmation dialog when the form is
 * dirty, and calls onClose immediately when it is clean.
 *
 * Use this as the onCancel prop of an Ant Design Modal to guard against
 * accidental dismissal via Escape or overlay click.
 *
 * The Cancel button inside the form should still call onClose directly —
 * that is an intentional action and needs no extra friction.
 *
 * @param onClose - the function to call when the modal should close
 * @param getIsDirty - called at event time to check current dirty state;
 *   use `() => formik.dirty` or `() => form.isFieldsTouched()`
 */
const useConfirmDirtyClose = (
  onClose: () => void,
  getIsDirty: () => boolean,
) => {
  const modal = useModal();
  const destroyRef = useRef<(() => void) | null>(null);

  useEffect(
    () => () => {
      destroyRef.current?.();
    },
    [],
  );

  return () => {
    if (!getIsDirty()) {
      onClose();
      return;
    }
    destroyRef.current?.();
    const { destroy } = modal.confirm({
      title: "Unsaved Changes",
      content:
        "You have unsaved changes that will be lost. Are you sure you want to close?",
      okText: "Discard changes",
      cancelText: "Keep editing",
      centered: true,
      icon: null,
      onOk: onClose,
    });
    destroyRef.current = destroy;
  };
};

export default useConfirmDirtyClose;
