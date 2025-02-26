import { h, VNode } from "preact";

import {
  FidesInitOptions,
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
      options={options}
      isTCF
      isMinimalTCF={experience.minimal_tcf}
      isGVLLoading={isGVLLoading}
    />
  );
};
