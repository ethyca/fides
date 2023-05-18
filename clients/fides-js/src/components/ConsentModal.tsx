import { h } from "preact";
import { useMemo, useState } from "preact/hooks";
import {
  ButtonType,
  ExperienceConfig,
  PrivacyNotice,
} from "../lib/consent-types";
import NoticeToggles from "./NoticeToggles";
import Button from "./Button";
import { getOrMakeFidesCookie } from "../lib/cookie";

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
  onSave,
  onAcceptAll,
  onRejectAll,
}: {
  experience: ExperienceConfig;
  notices: PrivacyNotice[];
  onClose: () => void;
  onSave: (enabledNoticeIds: Array<PrivacyNotice["id"]>) => void;
  onAcceptAll: () => void;
  onRejectAll: () => void;
}) => {
  const initialEnabledNoticeIds = useMemo(() => {
    const cookie = getOrMakeFidesCookie();
    return Object.keys(cookie.consent).filter((key) => cookie.consent[key]);
  }, []);

  const [enabledNoticeIds, setEnabledNoticeIds] = useState<
    Array<PrivacyNotice["id"]>
  >(initialEnabledNoticeIds);

  const handleSave = () => {
    onSave(enabledNoticeIds);
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
              onClick={handleSave}
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
