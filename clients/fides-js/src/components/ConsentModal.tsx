import { h } from "preact";
import { useState } from "preact/hooks";
import {
  ButtonType,
  ExperienceConfig,
  PrivacyNotice,
} from "../lib/consent-types";
import NoticeToggles from "./NoticeToggles";
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
  onClose,
  onAcceptAll,
  onRejectAll,
}: {
  experience: ExperienceConfig;
  notices: PrivacyNotice[];
  onClose: () => void;
  onAcceptAll: () => void;
  onRejectAll: () => void;
}) => {
  // DEFER: set initial state based on GET /consent-request/id/privacy-preferences?
  const [enabledNoticeIds, setEnabledNoticeIds] = useState<
    Array<PrivacyNotice["id"]>
  >([]);

  const handleSubmit = () => {
    // DEFER: implement fetch PATCH against /consent-request/id/privacy-preferences?
    const noticeMap = notices.map((notice) => ({
      [notice.id]: enabledNoticeIds.includes(notice.id),
    }));
    console.log("submitting notice map", noticeMap);
    onClose();
  };

  const handleAcceptAll = () => {
    onAcceptAll();
    onClose();
  };

  const handleRejectAll = () => {
    onRejectAll();
    onClose();
  };

  return (
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
          <div className="modal-notices">
            <NoticeToggles
              notices={notices}
              enabledNoticeIds={enabledNoticeIds}
              onChange={setEnabledNoticeIds}
            />
          </div>
          <div className="modal-button-group">
            <Button
              label="Save"
              buttonType={ButtonType.SECONDARY}
              onClick={handleSubmit}
            />
            <Button
              label={experience.reject_button_label}
              buttonType={ButtonType.PRIMARY}
              onClick={handleRejectAll}
            />
            <Button
              label={experience.confirmation_button_label}
              buttonType={ButtonType.PRIMARY}
              onClick={handleAcceptAll}
            />
          </div>
        </div>
      </div>
      <div className="modal-overlay" id="modal-overlay" />
    </div>
  );
};

export default ConsentModal;
