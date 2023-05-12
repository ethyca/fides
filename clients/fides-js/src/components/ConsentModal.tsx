import { h } from "preact";
import {
  ButtonType,
  ExperienceConfig,
  PrivacyNotice,
} from "../lib/consent-types";
import NoticeToggleTable from "./NoticeToggleTable";
import Button from "./Button";

/**
 * TODO: a11y reqs
 * 1. trap focus within the modal
 * 2. add a close button?
 * 3. figure out how clicking outside the modal should work a11y wise
 * 4. ESC to close the dialog
 */
const ConsentModal = ({
  experience,
  notices,
}: {
  experience: ExperienceConfig;
  notices: PrivacyNotice[];
}) => (
  <div>
    <div
      data-testid="consent-modal"
      id="fides-consent-modal"
      role="dialog"
      aria-modal="true"
    >
      <div data-testid="modal-content">
        <h1 data-testid="modal-header" className="modal-header">
          {experience.component_title}
        </h1>
        <p data-testid="modal-description">
          {experience.component_description}
        </p>
        <NoticeToggleTable notices={notices} />
        <div className="modal-button-group">
          <Button label="Save" buttonType={ButtonType.SECONDARY} />
          <Button
            label={experience.reject_button_label}
            buttonType={ButtonType.PRIMARY}
          />
          <Button
            label={experience.confirmation_button_label}
            buttonType={ButtonType.PRIMARY}
          />
        </div>
      </div>
    </div>
    <div
      className="modal-overlay"
      id="modal-overlay"
      // TODO: is this safe a11y wise?
      // onClick={onClose}
    />
  </div>
);

export default ConsentModal;
