import { h } from "preact";
import Button from "./Button";
import {
  ButtonType,
  PrivacyExperience,
  ConsentMechanism,
  PrivacyNotice,
} from "../lib/consent-types";

type NoticeKeys = Array<PrivacyNotice["notice_key"]>;

const ConsentButtons = ({
  experience,
  onManagePreferencesClick,
  onSave,
  enabledKeys,
  isInModal,
}: {
  experience: PrivacyExperience;
  onSave: (noticeKeys: NoticeKeys) => void;
  onManagePreferencesClick?: () => void;
  enabledKeys: NoticeKeys;
  isInModal?: boolean;
}) => {
  if (!experience.experience_config || !experience.privacy_notices) {
    return null;
  }

  const { experience_config: config, privacy_notices: notices } = experience;
  const isAllNoticeOnly = notices.every(
    (n) => n.consent_mechanism === ConsentMechanism.NOTICE_ONLY
  );

  const handleAcceptAll = () => {
    onSave(notices.map((n) => n.notice_key));
  };

  const handleRejectAll = () => {
    onSave(
      notices
        .filter((n) => n.consent_mechanism === ConsentMechanism.NOTICE_ONLY)
        .map((n) => n.notice_key)
    );
  };

  if (isAllNoticeOnly) {
    return (
      <div
        className={`fides-acknowledge-button-container ${
          isInModal ? "" : "fides-banner-acknowledge"
        }`}
      >
        <Button
          buttonType={ButtonType.PRIMARY}
          label={config.acknowledge_button_label}
          onClick={handleAcceptAll}
        />
      </div>
    );
  }

  return (
    <div id="fides-banner-buttons" className="fides-banner-buttons">
      {onManagePreferencesClick ? (
        <div>
          <Button
            buttonType={ButtonType.TERTIARY}
            label={config.privacy_preferences_link_label}
            onClick={onManagePreferencesClick}
          />
        </div>
      ) : null}
      <div className={isInModal ? "fides-modal-button-group" : undefined}>
        {isInModal ? (
          <Button
            buttonType={ButtonType.SECONDARY}
            label={config.save_button_label}
            onClick={() => {
              onSave(enabledKeys);
            }}
          />
        ) : null}
        <Button
          buttonType={ButtonType.PRIMARY}
          label={config.reject_button_label}
          onClick={handleRejectAll}
        />
        <Button
          buttonType={ButtonType.PRIMARY}
          label={config.accept_button_label}
          onClick={handleAcceptAll}
        />
      </div>
    </div>
  );
};

export default ConsentButtons;
