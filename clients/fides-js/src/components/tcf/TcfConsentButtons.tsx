import { h, VNode } from "preact";

import {
  FidesInitOptions,
  Layer1ButtonOption,
  PrivacyExperience,
  PrivacyExperienceMinimal,
} from "../../lib/consent-types";
import { ConsentButtons } from "../ConsentButtons";

interface TcfConsentButtonProps {
  experience: PrivacyExperience | PrivacyExperienceMinimal;
  options: FidesInitOptions;
  onManagePreferencesClick?: () => void;
  onRejectAll: () => void;
  onAcceptAll: () => void;
  renderFirstButton?: () => VNode;
  isInModal?: boolean;
}

export const TcfConsentButtons = ({
  experience,
  onManagePreferencesClick,
  onRejectAll,
  onAcceptAll,
  renderFirstButton,
  isInModal,
  options,
}: TcfConsentButtonProps) => {
  if (!experience.experience_config) {
    return null;
  }

  const isGVLLoading = Object.keys(experience.gvl || {}).length === 0;

  return (
    <ConsentButtons
      availableLocales={experience.available_locales}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={onAcceptAll}
      onRejectAll={onRejectAll}
      renderFirstButton={renderFirstButton}
      isInModal={isInModal}
      hideRejectAll={
        !isInModal &&
        experience.experience_config.layer1_button_options ===
          Layer1ButtonOption.OPT_IN_ONLY
      }
      options={options}
      isTCF
      isMinimalTCF={experience.minimal_tcf}
      isGVLLoading={isGVLLoading}
    />
  );
};
