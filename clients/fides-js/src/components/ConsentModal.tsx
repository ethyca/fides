import { VNode, h } from "preact";
import { Attributes } from "../lib/a11y-dialog";
import { ExperienceConfig } from "../lib/consent-types";

import CloseButton from "./CloseButton";
import ConsentContent from "~/components/ConsentContent";

const ConsentModal = ({
  attributes,
  experience,
  renderModalFooter,
  renderModalContent,
}: {
  attributes: Attributes;
  experience: ExperienceConfig;
  onVendorPageClick?: () => void;
  renderModalFooter: () => VNode;
  renderModalContent: () => VNode;
}) => {
  const { container, overlay, dialog, title, closeButton } = attributes;

  return (
    // @ts-ignore A11yDialog ref obj type isn't quite the same
    <div
      data-testid="consent-modal"
      {...container}
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
          <CloseButton ariaLabel="Close modal" onClick={closeButton.onClick} />
        </div>
        <ConsentContent
          title={title}
          experience={experience}
          renderModalFooter={renderModalFooter}
        >
          {" "}
          {renderModalContent()}
        </ConsentContent>
      </div>
    </div>
  );
};

export default ConsentModal;
