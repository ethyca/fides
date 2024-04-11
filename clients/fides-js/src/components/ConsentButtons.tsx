import { h, Fragment, VNode } from "preact";
import Button from "./Button";
import {
  ButtonType,
  ConsentMechanism,
  ConsentMethod,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyNotice,
} from "../lib/consent-types";
import PrivacyPolicyLink from "./PrivacyPolicyLink";
import type { I18n } from "../lib/i18n";
import LanguageSelector from "../components/LanguageSelector";

export const ConsentButtons = ({
  i18n,
  onManagePreferencesClick,
  firstButton,
  onAcceptAll,
  onRejectAll,
  isMobile,
  includePrivacyPolicy,
  saveOnly = false,
  options,
  isInModal,
}: {
  i18n: I18n;
  onManagePreferencesClick?: () => void;
  firstButton?: VNode;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  isMobile: boolean;
  options: FidesInitOptions;
  includePrivacyPolicy?: boolean;
  saveOnly?: boolean;
  isInModal?: boolean;
}) => (
  <div id="fides-button-group">
    {i18n.availableLanguages?.length > 1 && (
      <LanguageSelector i18n={i18n} options={options} />
    )}
    {!!onManagePreferencesClick && (
      <div className="fides-banner-button-group fides-manage-preferences-button-group">
        <Button
          buttonType={isMobile ? ButtonType.SECONDARY : ButtonType.TERTIARY}
          label={i18n.t("exp.privacy_preferences_link_label")}
          onClick={onManagePreferencesClick}
          className="fides-manage-preferences-button"
        />
      </div>
    )}
    {includePrivacyPolicy && <PrivacyPolicyLink i18n={i18n} />}
    <div
      className={
        isInModal
          ? "fides-modal-button-group fides-modal-primary-actions"
          : "fides-banner-button-group fides-banner-primary-actions"
      }
    >
      {firstButton}
      {!saveOnly && (
        <Fragment>
          <Button
            buttonType={ButtonType.PRIMARY}
            label={i18n.t("exp.reject_button_label")}
            onClick={onRejectAll}
            className="fides-reject-all-button"
          />
          <Button
            buttonType={ButtonType.PRIMARY}
            label={i18n.t("exp.accept_button_label")}
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
  options: FidesInitOptions;
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
  options,
}: NoticeConsentButtonProps) => {
  if (!experience.experience_config || !experience.privacy_notices) {
    return null;
  }
  const { privacy_notices: notices } = experience;

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
          label={i18n.t("exp.acknowledge_button_label")}
          onClick={handleAcceptAll}
          className="fides-acknowledge-button"
        />
      </div>
    );
  }

  return (
    <ConsentButtons
      i18n={i18n}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={handleAcceptAll}
      onRejectAll={handleRejectAll}
      isInModal={isInModal}
      firstButton={
        isInModal ? (
          <Button
            buttonType={saveOnly ? ButtonType.PRIMARY : ButtonType.SECONDARY}
            label={i18n.t("exp.save_button_label")}
            onClick={handleSave}
            className="fides-save-button"
          />
        ) : undefined
      }
      isMobile={isMobile}
      includePrivacyPolicy={!isInModal}
      saveOnly={saveOnly}
      options={options}
    />
  );
};
