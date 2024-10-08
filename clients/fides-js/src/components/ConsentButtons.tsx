import { Fragment, h, VNode } from "preact";
import { useEffect, useState } from "preact/hooks";

import {
  ButtonType,
  ConsentMechanism,
  ConsentMethod,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyNotice,
} from "../lib/consent-types";
import { useMediaQuery } from "../lib/hooks/useMediaQuery";
import { DEFAULT_LOCALE, Locale, messageExists } from "../lib/i18n";
import { useI18n } from "../lib/i18n/i18n-context";
import Button from "./Button";
import LanguageSelector from "./LanguageSelector";
import PrivacyPolicyLink from "./PrivacyPolicyLink";

interface ConsentButtonProps {
  availableLocales?: Locale[];
  onManagePreferencesClick?: () => void;
  renderFirstButton?: () => VNode | null;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  options: FidesInitOptions;
  hideOptInOut?: boolean;
  isInModal?: boolean;
  isTCF?: boolean;
  isMinimalTCF?: boolean;
  isGVLLoading?: boolean;
}
export const ConsentButtons = ({
  availableLocales = [DEFAULT_LOCALE],
  onManagePreferencesClick,
  renderFirstButton,
  onAcceptAll,
  onRejectAll,
  hideOptInOut = false,
  options,
  isInModal,
  isTCF,
  isMinimalTCF,
  isGVLLoading,
}: ConsentButtonProps) => {
  const [isLoadingModal, setIsLoadingModal] = useState<boolean>(false);
  const { i18n } = useI18n();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const includeLanguageSelector = i18n.availableLanguages?.length > 1;
  const includePrivacyPolicyLink =
    messageExists(i18n, "exp.privacy_policy_link_label") &&
    messageExists(i18n, "exp.privacy_policy_url");
  const handleManagePreferencesClick = () => {
    const isReady = !isTCF || !isMinimalTCF;
    setIsLoadingModal(!isReady);
    if (onManagePreferencesClick && isReady) {
      onManagePreferencesClick();
    }
  };

  useEffect(() => {
    if (isLoadingModal && !isMinimalTCF) {
      handleManagePreferencesClick();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoadingModal, isMinimalTCF]);

  return (
    <div id="fides-button-group">
      <div
        className={
          isInModal
            ? "fides-modal-button-group fides-modal-primary-actions"
            : "fides-banner-button-group fides-banner-primary-actions"
        }
      >
        {!!renderFirstButton && renderFirstButton()}
        {!hideOptInOut && (
          <Fragment>
            {isTCF && !!onManagePreferencesClick && (
              <Button
                buttonType={ButtonType.SECONDARY}
                label={i18n.t("exp.privacy_preferences_link_label")}
                onClick={handleManagePreferencesClick}
                className="fides-manage-preferences-button"
                loading={isLoadingModal}
              />
            )}
            <Button
              buttonType={ButtonType.PRIMARY}
              label={i18n.t("exp.reject_button_label")}
              onClick={onRejectAll}
              className="fides-reject-all-button"
              loading={isGVLLoading}
            />
            <Button
              buttonType={ButtonType.PRIMARY}
              label={i18n.t("exp.accept_button_label")}
              onClick={onAcceptAll}
              className="fides-accept-all-button"
              loading={isGVLLoading}
            />
          </Fragment>
        )}
      </div>
      <div
        className={`${
          isInModal
            ? "fides-modal-button-group fides-modal-secondary-actions"
            : "fides-banner-button-group fides-banner-secondary-actions"
        }${includeLanguageSelector ? " fides-button-group-i18n" : ""}${
          includePrivacyPolicyLink ? " fides-button-group-privacy-policy" : ""
        }`}
      >
        {includeLanguageSelector && (
          <LanguageSelector
            availableLocales={availableLocales}
            options={options}
            isTCF={!!isTCF}
          />
        )}
        {!isTCF && !!onManagePreferencesClick && (
          <Button
            buttonType={isMobile ? ButtonType.SECONDARY : ButtonType.TERTIARY}
            label={i18n.t("exp.privacy_preferences_link_label")}
            onClick={onManagePreferencesClick}
            className="fides-manage-preferences-button"
          />
        )}
        {includePrivacyPolicyLink && <PrivacyPolicyLink />}
      </div>
    </div>
  );
};

type NoticeKeys = Array<PrivacyNotice["notice_key"]>;

interface NoticeConsentButtonProps {
  experience: PrivacyExperience;
  onSave: (consentMethod: ConsentMethod, noticeKeys: NoticeKeys) => void;
  onManagePreferencesClick?: () => void;
  enabledKeys: NoticeKeys;
  isAcknowledge: boolean;
  options: FidesInitOptions;
  isInModal?: boolean;
  hideOptInOut?: boolean;
}

export const NoticeConsentButtons = ({
  experience,
  onSave,
  onManagePreferencesClick,
  enabledKeys,
  isInModal,
  isAcknowledge,
  hideOptInOut = false,
  options,
}: NoticeConsentButtonProps) => {
  const { i18n } = useI18n();
  if (!experience.experience_config || !experience.privacy_notices) {
    return null;
  }
  const { privacy_notices: notices } = experience;

  const handleAcceptAll = () => {
    onSave(
      ConsentMethod.ACCEPT,
      notices.map((n) => n.notice_key),
    );
  };

  const handleAcknowledgeNotices = () => {
    onSave(
      ConsentMethod.ACKNOWLEDGE,
      notices.map((n) => n.notice_key),
    );
  };

  const handleRejectAll = () => {
    onSave(
      ConsentMethod.REJECT,
      notices
        .filter((n) => n.consent_mechanism === ConsentMechanism.NOTICE_ONLY)
        .map((n) => n.notice_key),
    );
  };

  const handleSave = () => {
    onSave(ConsentMethod.SAVE, enabledKeys);
  };

  const renderFirstButton = () => {
    if (isAcknowledge) {
      return (
        <Button
          buttonType={ButtonType.PRIMARY}
          label={i18n.t("exp.acknowledge_button_label")}
          onClick={handleAcknowledgeNotices}
          className="fides-acknowledge-button"
        />
      );
    }
    if (isInModal) {
      return (
        <Button
          buttonType={hideOptInOut ? ButtonType.PRIMARY : ButtonType.SECONDARY}
          label={i18n.t("exp.save_button_label")}
          onClick={handleSave}
          className="fides-save-button"
        />
      );
    }
    return null;
  };

  return (
    <ConsentButtons
      availableLocales={experience.available_locales}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={handleAcceptAll}
      onRejectAll={handleRejectAll}
      isInModal={isInModal}
      renderFirstButton={renderFirstButton}
      hideOptInOut={hideOptInOut}
      options={options}
    />
  );
};
