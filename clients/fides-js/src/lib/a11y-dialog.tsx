/**
 * a11y-dialog adapted to preact
 * https://github.com/KittyGiraudel/a11y-dialog
 */

import A11yDialog from "a11y-dialog";
import { RefCallback } from "preact";
import { HTMLAttributes } from "preact/compat";
import { useCallback, useEffect, useState } from "preact/hooks";

const useA11yDialogInstance = () => {
  const [instance, setInstance] = useState<A11yDialog | null>(null);
  const container: RefCallback<HTMLDivElement | null> = useCallback(
    (node: HTMLDivElement | null) => {
      if (node !== null) {
        const dialog = new A11yDialog(node);
        setInstance(dialog);
      }
    },
    [],
  );
  return { instance, container };
};

export interface A11yDialogProperties {
  instance: A11yDialog | null;
  attributes: {
    container: Partial<HTMLAttributes<HTMLDivElement>>;
    dialog: Partial<HTMLAttributes<HTMLDivElement>>;
    closeButton: Partial<HTMLAttributes<HTMLButtonElement>> & {
      onClick: () => void;
    };
    title: Partial<HTMLAttributes<HTMLHeadingElement>>;
  };
}

interface Props {
  id: string;
  onClose?: () => void;
  ariaHidden?: boolean;
}
export const useA11yDialog = ({
  id,
  onClose,
  ariaHidden = true,
}: Props): A11yDialogProperties => {
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
        "aria-hidden": ariaHidden,
        "aria-labelledby": titleId,
      },
      dialog: { role: "document" } as const,
      closeButton: { type: "button", onClick: handleClose },
      title: { role: "heading", "aria-level": 1, id: titleId } as const,
    },
  };
};

export type A11yDialogAttributes = A11yDialogProperties["attributes"];
