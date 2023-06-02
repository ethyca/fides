import { h } from "preact";
import { useMemo, useState } from "preact/hooks";
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
  onSave,
  onAcceptAll,
  onRejectAll,
}: {
  experience: ExperienceConfig;
  notices: PrivacyNotice[];
  onClose: () => void;
  onSave: (enabledNoticeKeys: Array<PrivacyNotice["notice_key"]>) => void;
  onAcceptAll: () => void;
  onRejectAll: () => void;
}) => {
  const initialEnabledNoticeKeys = useMemo(
    () =>
      Object.keys(window.Fides.consent).filter(
        (key) => window.Fides.consent[key]
      ),
    []
  );

  const [enabledNoticeKeys, setEnabledNoticeKeys] = useState<
    Array<PrivacyNotice["notice_key"]>
  >(initialEnabledNoticeKeys);

  const handleSave = () => {
    onSave(enabledNoticeKeys);
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
            {experience.title}
          </h1>
          <p data-testid="modal-description" className="modal-description">
            {experience.description}
          </p>
          <div className="modal-notices">
            <NoticeToggles
              notices={notices}
              enabledNoticeKeys={enabledNoticeKeys}
              onChange={setEnabledNoticeKeys}
            />
          </div>
          <div className="modal-button-group">
            <Button
              label={experience.save_button_label}
              buttonType={ButtonType.SECONDARY}
              onClick={handleSave}
            />
            <Button
              label={experience.reject_button_label}
              buttonType={ButtonType.PRIMARY}
              onClick={handleRejectAll}
            />
            <Button
              label={experience.accept_button_label}
              buttonType={ButtonType.PRIMARY}
              onClick={handleAcceptAll}
            />
          </div>
          {experience.privacy_policy_link_label &&
          experience.privacy_policy_url ? (
            <a
              href={experience.privacy_policy_url}
              rel="noopener noreferrer"
              target="_blank"
              className="modal-privacy-policy"
            >
              {experience.privacy_policy_link_label}
            </a>
          ) : null}
        </div>
      </div>
      <div className="modal-overlay" id="modal-overlay" />
    </div>
  );
};

export default ConsentModal;
