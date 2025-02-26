/**
 * react-a11y-dialog adapted to preact
 * https://github.com/KittyGiraudel/react-a11y-dialog
 */

import A11yDialogLib from "a11y-dialog";
import { useCallback, useEffect, useState } from "preact/hooks";

const useA11yDialogInstance = () => {
  const [instance, setInstance] = useState<A11yDialogLib | null>(null);
  const container = useCallback((node: Element) => {
    if (node !== null) {
      const dialog = new A11yDialogLib(node);
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
  role: "dialog" | "alertdialog";
  id: string;
  title: string;
  onClose?: () => void;
}
export const useA11yDialog = ({ role, id, onClose }: Props) => {
  const { instance, container: ref } = useA11yDialogInstance();
  const isAlertDialog = role === "alertdialog";
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
        role,
        tabIndex: -1,
        "aria-modal": true,
        "aria-hidden": true,
        "aria-labelledby": titleId,
      },
      overlay: { onClick: isAlertDialog ? undefined : handleClose },
      dialog: { role: "document" } as const,
      closeButton: { type: "button", onClick: handleClose },
      title: { role: "heading", "aria-level": 1, id: titleId } as const,
    },
  };
};

export type Attributes = ReturnType<typeof useA11yDialog>["attributes"];
