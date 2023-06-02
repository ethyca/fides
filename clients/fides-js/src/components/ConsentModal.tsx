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
        data-testid="fides-overlay-modal"
        id="fides-overlay-modal"
        role="dialog"
        aria-modal="true"
      >
        <div data-testid="fides-overlay-modal-content">
          <h1
            data-testid="fides-overlay-modal-header"
            className="fides-overlay-modal-header"
          >
            {experience.title}
          </h1>
          <p
            data-testid="fides-overlay-modal-description"
            className="fides-overlay-modal-description"
          >
            {experience.description}
          </p>
          <div className="fides-overlay-modal-notices">
            <NoticeToggles
              notices={notices}
              enabledNoticeKeys={enabledNoticeKeys}
              onChange={setEnabledNoticeKeys}
            />
          </div>
          <div className="fides-overlay-modal-button-group">
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
              className="fides-overlay-modal-privacy-policy"
            >
              {experience.privacy_policy_link_label}
            </a>
          ) : null}
        </div>
      </div>
      <div
        className="fides-overlay-modal-overlay"
        id="fides-overlay-modal-overlay"
      />
    </div>
  );
};

export default ConsentModal;
