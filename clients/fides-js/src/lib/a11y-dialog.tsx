/**
 * react-a11y-dialog adapted to preact
 * https://github.com/KittyGiraudel/react-a11y-dialog
 */

import A11yDialogLib from "a11y-dialog";
import { useCallback, useEffect, useState } from "preact/hooks";

const useA11yDialogInstance = (onEsc?: () => void) => {
  const [instance, setInstance] = useState<A11yDialogLib | null>(null);
  const container = useCallback((node: Element) => {
    if (node !== null) {
      const dialog = new A11yDialogLib(node);
      dialog
        .on("show", (event) => {
          document.documentElement.style.overflowY = "hidden";
        })
        .on("hide", (node: any, event: any) => {
          document.documentElement.style.overflowY = "";

          // a11y-dialog natively supports dismissing a dialog by pressing ESC
          // but it doesn't allow any custom functions to be associated
          // with an ESC press, so we have to do this manually
          if (
            onEsc &&
            event instanceof KeyboardEvent &&
            event.key === "Escape"
          ) {
            onEsc();
          }
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
  onEsc?: () => void;
}
export const useA11yDialog = ({ role, id, onClose, onEsc }: Props) => {
  const { instance, container: ref } = useA11yDialogInstance(onEsc);
  const isAlertDialog = role === "alertdialog";
  const titleId = `${id}-title`;

  const handleClose = useCallback(() => {
    if (instance) {
      instance.hide();
    }
    if (onClose) {
      onClose();
    }
  }, [instance]);

  // Destroy the `a11y-dialog` instance when unmounting the component
  useEffect(
    () => () => {
      if (instance) {
        instance.destroy();
      }
    },
    [instance]
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
