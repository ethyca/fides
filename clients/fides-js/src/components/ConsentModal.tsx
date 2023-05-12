import { h } from "preact";
import {
  ButtonType,
  ExperienceConfig,
  PrivacyNotice,
} from "../lib/consent-types";
import NoticeToggleTable from "./NoticeToggleTable";
import Button from "./Button";

const ConsentModal = ({
  experience,
  notices,
}: {
  experience: ExperienceConfig;
  notices: PrivacyNotice[];
}) => (
  <div data-testid="consent-modal" id="fides-consent-modal">
    <h1 data-testid="modal-header" className="modal-header">
      {experience.component_title}
    </h1>
    <p data-testid="modal-description">{experience.component_description}</p>
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
);

export default ConsentModal;
