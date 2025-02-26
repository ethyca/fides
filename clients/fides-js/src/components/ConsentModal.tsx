import { ComponentChildren, h, VNode } from "preact";
import { HTMLAttributes } from "preact/compat";

import { Attributes } from "../lib/a11y-dialog";
import CloseButton from "./CloseButton";
import ConsentContent from "./ConsentContent";

const ConsentModal = ({
  attributes,
  children,
  dismissable,
  onVendorPageClick,
  renderModalFooter,
}: {
  attributes: Attributes;
  children: ComponentChildren;
  dismissable: boolean | undefined;
  onVendorPageClick?: () => void;
  renderModalFooter: () => VNode | null;
}) => {
  const { container, overlay, dialog, title, closeButton } = attributes;

  return (
    <div
      data-testid="consent-modal"
      {...(container as Partial<HTMLAttributes<HTMLDivElement>>)}
      className="fides-modal-container"
    >
      <div {...overlay} className="fides-modal-overlay" />
      <div
        data-testid="fides-modal-content"
        {...dialog}
        className="fides-modal-content"
      >
        <div className="fides-modal-header">
          <div />
          <CloseButton
            ariaLabel="Close modal"
            onClick={closeButton.onClick}
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
