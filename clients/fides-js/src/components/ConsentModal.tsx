import { h } from "preact";
import { ExperienceConfig, PrivacyNotice } from "../lib/consent-types";
import NoticeToggleTable from "./NoticeToggleTable";

const ConsentModal = ({
  experience,
  notices,
}: {
  experience: ExperienceConfig;
  notices: PrivacyNotice[];
}) => {
  return (
    <div data-testid="consent-modal" id="fides-consent-modal">
      <p>{experience.component_description}</p>
      <NoticeToggleTable notices={notices} />
      <div>
        <button>Save</button>
        <button>{experience.reject_button_label}</button>
        <button>{experience.confirmation_button_label}</button>
      </div>
    </div>
  );
};

export default ConsentModal;
