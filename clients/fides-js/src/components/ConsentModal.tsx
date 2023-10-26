import { ComponentChildren, VNode, h } from "preact";
import { Attributes } from "../lib/a11y-dialog";
import { ExperienceConfig } from "../lib/consent-types";

import CloseButton from "./CloseButton";
import GpcInfo from "./GpcInfo";
import ExperienceDescription from "./ExperienceDescription";
import { getConsentContext } from "../fides";

const ConsentModal = ({
  attributes,
  experience,
  children,
  onVendorPageClick,
  renderModalFooter,
}: {
  attributes: Attributes;
  experience: ExperienceConfig;
  children: ComponentChildren;
  onVendorPageClick?: () => void;
  renderModalFooter: () => VNode;
}) => {
  const { container, overlay, dialog, title, closeButton } = attributes;
  const showGpcBadge = getConsentContext().globalPrivacyControl;

  return (
    // @ts-ignore A11yDialog ref obj type isn't quite the same
    <div
      data-testid="consent-modal"
      {...container}
      className={`fides-modal-container ${attributes.container.className}`}
    >
      <div {...overlay} className="fides-modal-overlay" />
      <div
        data-testid="fides-modal-content"
        {...dialog}
        className="fides-modal-content"
      >
        <div className="fides-modal-header">
          <div />
          <CloseButton ariaLabel="Close modal" onClick={closeButton.onClick} />
        </div>
        <div className="fides-modal-body">
          <h1
            data-testid="fides-modal-title"
            {...title}
            className="fides-modal-title"
          >
            {experience.title}
          </h1>
          <p
            data-testid="fides-modal-description"
            className="fides-modal-description"
          >
            <ExperienceDescription
              onVendorPageClick={onVendorPageClick}
              description={experience.description}
            />
          </p>
          {showGpcBadge && <GpcInfo />}
          {children}
        </div>
        <div className="fides-modal-footer">{renderModalFooter()}</div>
      </div>
    </div>
  );
};

export default ConsentModal;
