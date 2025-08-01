import { Fragment, VNode } from "preact";

import {
  ButtonType,
  ConsentMethod,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyNotice,
} from "../lib/consent-types";
import { FidesEventTargetType } from "../lib/events";
import { useMediaQuery } from "../lib/hooks/useMediaQuery";
import { DEFAULT_LOCALE, Locale, messageExists } from "../lib/i18n";
import { useI18n } from "../lib/i18n/i18n-context";
import { useEvent } from "../lib/providers/event-context";
import BrandLink from "./BrandLink";
import Button from "./Button";
import LanguageSelector from "./LanguageSelector";
import PrivacyPolicyLink from "./PrivacyPolicyLink";

interface ConsentButtonsProps {
  availableLocales?: Locale[];
  onManagePreferencesClick?: () => void;
  renderFirstButton?: () => VNode | null | false;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  options: FidesInitOptions;
  hideOptInOut?: boolean;
  hideRejectAll?: boolean;
  isInModal?: boolean;
  isTCF?: boolean;
  isGVLLoading?: boolean;
}
export const ConsentButtons = ({
  availableLocales = [DEFAULT_LOCALE],
  onManagePreferencesClick,
  renderFirstButton,
  onAcceptAll,
  onRejectAll,
  hideOptInOut,
  hideRejectAll,
  options,
  isInModal,
  isTCF,
  isGVLLoading,
}: ConsentButtonsProps) => {
  const { i18n } = useI18n();
  const { setTrigger } = useEvent();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const includeLanguageSelector = i18n.availableLanguages?.length > 1;
  const includePrivacyPolicyLink =
    messageExists(i18n, "exp.privacy_policy_link_label") &&
    messageExists(i18n, "exp.privacy_policy_url");
  const includeBrandLink = isInModal && options.showFidesBrandLink;

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
                onClick={() => {
                  setTrigger({
                    type: FidesEventTargetType.BUTTON,
                    label: i18n.t("exp.privacy_preferences_link_label"),
                  });
                  onManagePreferencesClick();
                }}
                className="fides-manage-preferences-button"
                id="fides-manage-preferences-button"
              />
            )}
            {!hideRejectAll && (
              <Button
                buttonType={ButtonType.PRIMARY}
                label={i18n.t("exp.reject_button_label")}
                onClick={() => {
                  setTrigger({
                    type: FidesEventTargetType.BUTTON,
                    label: i18n.t("exp.reject_button_label"),
                  });
                  onRejectAll();
                }}
                className="fides-reject-all-button"
                id="fides-reject-all-button"
                loading={isGVLLoading}
              />
            )}
            <Button
              buttonType={ButtonType.PRIMARY}
              label={i18n.t("exp.accept_button_label")}
              onClick={() => {
                setTrigger({
                  type: FidesEventTargetType.BUTTON,
                  label: i18n.t("exp.accept_button_label"),
                });
                onAcceptAll();
              }}
              className="fides-accept-all-button"
              id="fides-accept-all-button"
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
        }${includeBrandLink ? " fides-button-group-brand" : ""}`}
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
            onClick={() => {
              setTrigger({
                type: FidesEventTargetType.BUTTON,
                label: i18n.t("exp.privacy_preferences_link_label"),
              });
              onManagePreferencesClick();
            }}
            className="fides-manage-preferences-button"
            id="fides-manage-preferences-button"
          />
        )}
        {includePrivacyPolicyLink && <PrivacyPolicyLink />}
        {includeBrandLink && <BrandLink />}
      </div>
    </div>
  );
};

type NoticeKeys = Array<PrivacyNotice["notice_key"]>;

interface NoticeConsentButtonProps {
  experience: PrivacyExperience;
  onAcceptAll: () => void;
  onRejectAll: () => void;
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
  onAcceptAll,
  onRejectAll,
  onSave,
  onManagePreferencesClick,
  enabledKeys,
  isInModal,
  isAcknowledge,
  hideOptInOut = false,
  options,
}: NoticeConsentButtonProps) => {
  const { i18n } = useI18n();
  const { setTrigger } = useEvent();
  if (!experience.experience_config || !experience.privacy_notices) {
    return null;
  }
  const { privacy_notices: notices } = experience;

  const handleAcknowledgeNotices = () => {
    onSave(
      ConsentMethod.ACKNOWLEDGE,
      notices.map((n) => n.notice_key),
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
          onClick={() => {
            setTrigger({
              type: FidesEventTargetType.BUTTON,
              label: i18n.t("exp.acknowledge_button_label"),
            });
            handleAcknowledgeNotices();
          }}
          className="fides-acknowledge-button"
        />
      );
    }
    if (isInModal) {
      return (
        <Button
          buttonType={hideOptInOut ? ButtonType.PRIMARY : ButtonType.SECONDARY}
          label={i18n.t("exp.save_button_label")}
          onClick={() => {
            setTrigger({
              type: FidesEventTargetType.BUTTON,
              label: i18n.t("exp.save_button_label"),
            });
            handleSave();
          }}
          className="fides-save-button"
          id="fides-save-button"
        />
      );
    }
    return null;
  };

  return (
    <ConsentButtons
      availableLocales={experience.available_locales}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={onAcceptAll}
      onRejectAll={onRejectAll}
      isInModal={isInModal}
      renderFirstButton={renderFirstButton}
      hideOptInOut={hideOptInOut}
      options={options}
    />
  );
};
