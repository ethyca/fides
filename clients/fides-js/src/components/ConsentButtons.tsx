import { h, Fragment, VNode } from "preact";
import Button from "./Button";
import {
  ButtonType,
  ConsentMechanism,
  ConsentMethod,
  PrivacyExperience,
  PrivacyNotice,
} from "../lib/consent-types";
import PrivacyPolicyLink from "./PrivacyPolicyLink";
import type { I18n } from "../lib/i18n";
import MenuItem from "./MenuItem";
import { useI18n } from "../lib/i18n/i18n-context";

export const ConsentButtons = ({
  i18n,
  onManagePreferencesClick,
  firstButton,
  onAcceptAll,
  onRejectAll,
  isMobile,
  includePrivacyPolicy,
  saveOnly = false,
  includeLanguageSelector = true,
}: {
  i18n: I18n;
  onManagePreferencesClick?: () => void;
  firstButton?: VNode;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  isMobile: boolean;
  includePrivacyPolicy?: boolean;
  saveOnly?: boolean;
  includeLanguageSelector?: boolean;
}) => {
  const { setCurrentLocale } = useI18n();
  const handleLocaleSelect = (locale: string) => {
    i18n.activate(locale);
    setCurrentLocale(i18n.locale);
    document.getElementById("fides-button-group")?.focus();
  };
  return (
    <div id="fides-button-group" tabIndex={-1}>
      {includeLanguageSelector && i18n.availableLanguages?.length > 1 && (
        <div className="fides-i18n-menu">
          <div role="group" className="fides-i18n-popover">
            {i18n.availableLanguages.map((lang) => (
              <MenuItem
                key={lang.locale}
                id={`fides-i18n-option-${lang.locale}`}
                onClick={() => handleLocaleSelect(lang.locale)}
                isActive={i18n.locale === lang.locale}
              >
                {lang.original}
              </MenuItem>
            ))}
          </div>
          <div className="fides-i18n-pseudo-button">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 640 512"
              height="inherit"
              fill="currentColor"
            >
              <path d="M0 128C0 92.7 28.7 64 64 64H256h48 16H576c35.3 0 64 28.7 64 64V384c0 35.3-28.7 64-64 64H320 304 256 64c-35.3 0-64-28.7-64-64V128zm320 0V384H576V128H320zM178.3 175.9c-3.2-7.2-10.4-11.9-18.3-11.9s-15.1 4.7-18.3 11.9l-64 144c-4.5 10.1 .1 21.9 10.2 26.4s21.9-.1 26.4-10.2l8.9-20.1h73.6l8.9 20.1c4.5 10.1 16.3 14.6 26.4 10.2s14.6-16.3 10.2-26.4l-64-144zM160 233.2L179 276H141l19-42.8zM448 164c11 0 20 9 20 20v4h44 16c11 0 20 9 20 20s-9 20-20 20h-2l-1.6 4.5c-8.9 24.4-22.4 46.6-39.6 65.4c.9 .6 1.8 1.1 2.7 1.6l18.9 11.3c9.5 5.7 12.5 18 6.9 27.4s-18 12.5-27.4 6.9l-18.9-11.3c-4.5-2.7-8.8-5.5-13.1-8.5c-10.6 7.5-21.9 14-34 19.4l-3.6 1.6c-10.1 4.5-21.9-.1-26.4-10.2s.1-21.9 10.2-26.4l3.6-1.6c6.4-2.9 12.6-6.1 18.5-9.8l-12.2-12.2c-7.8-7.8-7.8-20.5 0-28.3s20.5-7.8 28.3 0l14.6 14.6 .5 .5c12.4-13.1 22.5-28.3 29.8-45H448 376c-11 0-20-9-20-20s9-20 20-20h52v-4c0-11 9-20 20-20z" />
            </svg>
          </div>
        </div>
      )}
      {!!onManagePreferencesClick && (
        <div className="fides-banner-button-group">
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
          firstButton ? "fides-modal-button-group" : "fides-banner-button-group"
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
};

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
  fidesPreviewMode?: boolean;
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
  fidesPreviewMode = false,
}: NoticeConsentButtonProps) => {
  if (!experience.experience_config || !experience.privacy_notices) {
    return null;
  }
  const { privacy_notices: notices } = experience;

  const handleAcceptAll = () => {
    if (fidesPreviewMode) {
      return;
    }
    onSave(
      ConsentMethod.ACCEPT,
      notices.map((n) => n.notice_key)
    );
  };

  const handleRejectAll = () => {
    if (fidesPreviewMode) {
      return;
    }
    onSave(
      ConsentMethod.REJECT,
      notices
        .filter((n) => n.consent_mechanism === ConsentMechanism.NOTICE_ONLY)
        .map((n) => n.notice_key)
    );
  };

  const handleSave = () => {
    if (fidesPreviewMode) {
      return;
    }
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
      includeLanguageSelector={!isInModal}
    />
  );
};
