import { VNode, h } from "preact";

import { Attributes } from "../lib/a11y-dialog";
import { ExperienceConfig } from "../lib/consent-types";
import type { I18n } from "../lib/i18n";

import CloseButton from "./CloseButton";
import ConsentContent from "./ConsentContent";

const ConsentModal = ({
  attributes,
  experience,
  i18n,
  renderModalFooter,
  renderModalContent,
}: {
  attributes: Attributes;
  experience: ExperienceConfig;
  i18n: I18n;
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
          <CloseButton
            ariaLabel="Close modal"
            onClick={
              window.Fides.options.fidesPreviewMode
                ? () => {}
                : closeButton.onClick
            }
            hidden={window.Fides.options.preventDismissal}
          />
        </div>
        <ConsentContent
          title={title}
          experience={experience}
          i18n={i18n}
          renderModalFooter={renderModalFooter}
        >
          {renderModalContent()}
        </ConsentContent>
      </div>
    </div>
  );
};

export default ConsentModal;
