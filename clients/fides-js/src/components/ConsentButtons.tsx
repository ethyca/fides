import { h, Fragment, VNode } from "preact";
import Button from "./Button";
import {
  ButtonType,
  ConsentMechanism,
  ConsentMethod,
  ExperienceConfig,
  PrivacyExperience,
  PrivacyNotice,
} from "../lib/consent-types";
import PrivacyPolicyLink from "./PrivacyPolicyLink";
import { i18n, type I18n } from "../lib/i18n";

export const ConsentButtons = ({
  experienceConfig,
  i18n,
  onManagePreferencesClick,
  firstButton,
  onAcceptAll,
  onRejectAll,
  isMobile,
  includePrivacyPolicy,
  saveOnly = false,
}: {
  experienceConfig: ExperienceConfig;
  i18n: I18n;
  onManagePreferencesClick?: () => void;
  firstButton?: VNode;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  isMobile: boolean;
  includePrivacyPolicy?: boolean;
  saveOnly?: boolean;
}) => (
  <div id="fides-button-group">
    {onManagePreferencesClick ? (
      <div style={{ display: "flex" }}>
        <Button
          buttonType={isMobile ? ButtonType.SECONDARY : ButtonType.TERTIARY}
          label={ i18n.t("exp.privacy_preferences_link_label") }
          onClick={onManagePreferencesClick}
          className="fides-manage-preferences-button"
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
      {!saveOnly && (
        <Fragment>
          <Button
            buttonType={ButtonType.PRIMARY}
            label={ i18n.t("exp.reject_button_label") }
            onClick={onRejectAll}
            className="fides-reject-all-button"
          />
          <Button
            buttonType={ButtonType.PRIMARY}
            label={ i18n.t("exp.accept_button_label") }
            onClick={onAcceptAll}
            className="fides-accept-all-button"
          />
        </Fragment>
      )}
    </div>
  </div>
);

type NoticeKeys = Array<PrivacyNotice["notice_key"]>;

interface NoticeConsentButtonProps {
  experience: PrivacyExperience;
  i18n: I18n;
  onSave: (consentMethod: ConsentMethod, noticeKeys: NoticeKeys) => void;
  onManagePreferencesClick?: () => void;
  enabledKeys: NoticeKeys;
  isAcknowledge: boolean;
  isInModal?: boolean;
  isMobile: boolean;
  saveOnly?: boolean;
}

export const NoticeConsentButtons = ({
  experience,
  i18n,
  onSave,
  onManagePreferencesClick,
  enabledKeys,
  isInModal,
  isAcknowledge,
  isMobile,
  saveOnly = false,
}: NoticeConsentButtonProps) => {
  if (!experience.experience_config || !experience.privacy_notices) {
    return null;
  }
  const { experience_config: config, privacy_notices: notices } = experience;

  const handleAcceptAll = () => {
    onSave(
      ConsentMethod.ACCEPT,
      notices.map((n) => n.notice_key)
    );
  };

  const handleRejectAll = () => {
    onSave(
      ConsentMethod.REJECT,
      notices
        .filter((n) => n.consent_mechanism === ConsentMechanism.NOTICE_ONLY)
        .map((n) => n.notice_key)
    );
  };

  const handleSave = () => {
    onSave(ConsentMethod.SAVE, enabledKeys);
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
          label={config?.translations[0].acknowledge_button_label}
          onClick={handleAcceptAll}
          className="fides-acknowledge-button"
        />
      </div>
    );
  }

  return (
    <ConsentButtons
      experienceConfig={config}
      i18n={i18n}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={handleAcceptAll}
      onRejectAll={handleRejectAll}
      firstButton={
        isInModal ? (
          <Button
            buttonType={saveOnly ? ButtonType.PRIMARY : ButtonType.SECONDARY}
            label={ i18n.t("exp.save_button_label") }
            onClick={handleSave}
            className="fides-save-button"
          />
        ) : undefined
      }
      isMobile={isMobile}
      includePrivacyPolicy={!isInModal}
      saveOnly={saveOnly}
    />
  );
};
