import { ComponentChildren, VNode } from "preact";
import { HTMLAttributes } from "preact/compat";

import { A11yDialogAttributes } from "../lib/a11y-dialog";
import { useEvent } from "../lib/providers/event-context";
import CloseButton from "./CloseButton";
import ConsentContent from "./ConsentContent";

const ConsentModal = ({
  attributes,
  children,
  dismissable,
  onVendorPageClick,
  renderModalFooter,
}: {
  attributes: A11yDialogAttributes;
  children: ComponentChildren;
  dismissable: boolean | undefined;
  onVendorPageClick?: () => void;
  renderModalFooter: () => VNode | null;
}) => {
  const { container, dialog, title, closeButton } = attributes;
  const { setTrigger } = useEvent();
  if (!window.Fides) {
    // since we rely on window.Fides for the hidden status of the close button,
    // we need to make sure it's available before rendering the modal. This can cause
    // issues in Admin UI preview, for example.
    return null;
  }
  return (
    <div
      data-testid="consent-modal"
      {...(container as Partial<HTMLAttributes<HTMLDivElement>>)}
      className="fides-modal-container"
    >
      <div className="fides-modal-overlay" />
      <div
        data-testid="fides-modal-content"
        {...dialog}
        className="fides-modal-content"
      >
        <div className="fides-modal-header">
          <div />
          <CloseButton
            ariaLabel="Close modal"
            onClick={() => {
              setTrigger({
                type: "button",
                label: "Close modal",
              });
              closeButton.onClick();
            }}
            hidden={window.Fides.options.preventDismissal || !dismissable}
          />
        </div>
        <ConsentContent
          titleProps={title}
          renderModalFooter={renderModalFooter}
          onVendorPageClick={onVendorPageClick}
        >
          {children}
        </ConsentContent>
      </div>
    </div>
  );
};

export default ConsentModal;
