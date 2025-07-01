/**
 * a11y-dialog adapted to preact
 * https://github.com/KittyGiraudel/a11y-dialog
 */

import A11yDialog from "a11y-dialog";
import { useCallback, useEffect, useState } from "preact/hooks";

const useA11yDialogInstance = () => {
  const [instance, setInstance] = useState<A11yDialog | null>(null);
  const container = useCallback((node: HTMLElement) => {
    if (node !== null) {
      const dialog = new A11yDialog(node);
      dialog
        .on("show", () => {
          document.documentElement.style.overflowY = "hidden";
        })
        .on("hide", () => {
          document.documentElement.style.overflowY = "";
        });
      setInstance(dialog);
    }
  }, []);
  return { instance, container };
};

interface Props {
  id: string;
  onClose?: () => void;
}
export const useA11yDialog = ({ id, onClose }: Props) => {
  const { instance, container: ref } = useA11yDialogInstance();
  const titleId = `${id}-title`;

  const handleClose = useCallback(() => {
    if (instance) {
      instance.hide();
    }
    if (onClose) {
      onClose();
    }
  }, [onClose, instance]);

  // Destroy the `a11y-dialog` instance when unmounting the component
  useEffect(
    () => () => {
      if (instance) {
        instance.destroy();
      }
    },
    [instance],
  );

  return {
    instance,
    attributes: {
      container: {
        id,
        ref,
        role: "alertdialog",
        tabIndex: -1,
        "aria-modal": true,
        "aria-hidden": true,
        "aria-labelledby": titleId,
      },
      dialog: { role: "document" } as const,
      closeButton: { type: "button", onClick: handleClose },
      title: { role: "heading", "aria-level": 1, id: titleId } as const,
    },
  };
};

export type Attributes = ReturnType<typeof useA11yDialog>["attributes"];
