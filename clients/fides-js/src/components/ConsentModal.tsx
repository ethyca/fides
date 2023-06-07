/* eslint-disable react/jsx-props-no-spreading */
import { h } from "preact";
import { useMemo, useState } from "preact/hooks";
import { Attributes } from "../lib/a11y-dialog";
import Button from "./Button";
import {
  ButtonType,
  PrivacyNotice,
  ExperienceConfig,
} from "../lib/consent-types";
import NoticeToggles from "./NoticeToggles";
import CloseButton from "./CloseButton";

const ConsentModal = ({
  attributes,
  experience,
  notices,
  onClose,
  onSave,
  onAcceptAll,
  onRejectAll,
}: {
  attributes: Attributes;
  experience: ExperienceConfig;
  notices: PrivacyNotice[];
  onClose: () => void;
  onSave: (enabledNoticeKeys: Array<PrivacyNotice["notice_key"]>) => void;
  onAcceptAll: () => void;
  onRejectAll: () => void;
}) => {
  const { container, overlay, dialog, title, closeButton } = attributes;

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
    // @ts-ignore A11yDialog ref obj type isn't quite the same
    <div data-testid="consent-modal" {...container} className="modal-container">
      <div {...overlay} className="modal-overlay" />
      <div data-testid="modal-content" {...dialog} className="modal-content">
        <CloseButton ariaLabel="Close modal" onClick={closeButton.onClick} />
        <h1 data-testid="modal-header" {...title} className="modal-header">
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
  );
};

export default ConsentModal;
