import { h } from "preact";
import { ExperienceConfig, PrivacyNotice } from "../lib/consent-types";
import NoticeToggleTable from "./NoticeToggleTable";

const ConsentModal = ({
  experience,
  notices,
}: {
  experience: ExperienceConfig;
  notices: PrivacyNotice[];
}) => (
  <div data-testid="consent-modal" id="fides-consent-modal">
    <p>{experience.component_description}</p>
    <NoticeToggleTable notices={notices} />
    <div>
      <button type="button">Save</button>
      <button type="button">{experience.reject_button_label}</button>
      <button type="button">{experience.confirmation_button_label}</button>
    </div>
  </div>
);

export default ConsentModal;
