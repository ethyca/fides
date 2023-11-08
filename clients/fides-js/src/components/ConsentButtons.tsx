import { h, VNode } from "preact";
import Button from "./Button";
import {
  ButtonType,
  PrivacyExperience,
  ConsentMechanism,
  PrivacyNotice,
  ExperienceConfig,
} from "../lib/consent-types";
import PrivacyPolicyLink from "./PrivacyPolicyLink";

export const ConsentButtons = ({
  experienceConfig,
  onManagePreferencesClick,
  firstButton,
  onAcceptAll,
  onRejectAll,
  isMobile,
  includePrivacyPolicy,
}: {
  experienceConfig: ExperienceConfig;
  onManagePreferencesClick?: () => void;
  firstButton?: VNode;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  isMobile: boolean;
  includePrivacyPolicy?: boolean;
}) => (
  <div id="fides-button-group">
    {onManagePreferencesClick ? (
      <div style={{ display: "flex" }}>
        <Button
          buttonType={isMobile ? ButtonType.SECONDARY : ButtonType.TERTIARY}
          label={experienceConfig.privacy_preferences_link_label}
          onClick={onManagePreferencesClick}
        />
      </div>
    ) : null}
    {includePrivacyPolicy ? (
      <PrivacyPolicyLink experience={experienceConfig} />
    ) : null}
    <div
      className={
        firstButton ? "fides-modal-button-group" : "fides-banner-button-group"
      }
    >
      {firstButton || null}
      <Button
        buttonType={ButtonType.PRIMARY}
        label={experienceConfig.reject_button_label}
        onClick={onRejectAll}
      />
      <Button
        buttonType={ButtonType.PRIMARY}
        label={experienceConfig.accept_button_label}
        onClick={onAcceptAll}
      />
    </div>
  </div>
);

type NoticeKeys = Array<PrivacyNotice["notice_key"]>;

interface NoticeConsentButtonProps {
  experience: PrivacyExperience;
  onSave: (noticeKeys: NoticeKeys) => void;
  onManagePreferencesClick?: () => void;
  enabledKeys: NoticeKeys;
  isAcknowledge: boolean;
  isInModal?: boolean;
  isMobile: boolean;
}

export const NoticeConsentButtons = ({
  experience,
  onSave,
  onManagePreferencesClick,
  enabledKeys,
  isInModal,
  isAcknowledge,
  isMobile,
}: NoticeConsentButtonProps) => {
  if (!experience.experience_config || !experience.privacy_notices) {
    return null;
  }
  const { experience_config: config, privacy_notices: notices } = experience;

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

  const handleSave = () => {
    onSave(enabledKeys);
  };

  if (isAcknowledge) {
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
    <ConsentButtons
      experienceConfig={config}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={handleAcceptAll}
      onRejectAll={handleRejectAll}
      firstButton={
        isInModal ? (
          <Button
            buttonType={ButtonType.SECONDARY}
            label={config.save_button_label}
            onClick={handleSave}
          />
        ) : undefined
      }
      isMobile={isMobile}
      includePrivacyPolicy={!isInModal}
    />
  );
};
