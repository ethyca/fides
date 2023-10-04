import { VNode, h } from "preact";

import { PrivacyExperience } from "../../lib/consent-types";
import { ConsentButtons } from "../ConsentButtons";
import type { EnabledIds, TcfModels } from "../../lib/tcf/types";

interface TcfConsentButtonProps {
  experience: PrivacyExperience;
  onManagePreferencesClick?: () => void;
  onSave: (keys: EnabledIds) => void;
  firstButton?: VNode;
}

const getAllIds = (modelList: TcfModels) => {
  if (!modelList) {
    return [];
  }
  return modelList.map((m) => `${m.id}`);
};

export const TcfConsentButtons = ({
  experience,
  onManagePreferencesClick,
  onSave,
  firstButton,
}: TcfConsentButtonProps) => {
  if (!experience.experience_config) {
    return null;
  }

  const handleAcceptAll = () => {
    const allIds: EnabledIds = {
      purposesConsent: getAllIds(experience.tcf_consent_purposes),
      purposesLegint: getAllIds(experience.tcf_legitimate_interests_purposes),
      specialPurposes: getAllIds(experience.tcf_special_purposes),
      features: getAllIds(experience.tcf_features),
      specialFeatures: getAllIds(experience.tcf_special_features),
      vendorsConsent: getAllIds([
        ...(experience.tcf_consent_vendors || []),
        ...(experience.tcf_consent_systems || []),
      ]),
      vendorsLegint: getAllIds([
        ...(experience.tcf_legitimate_interests_vendors || []),
        ...(experience.tcf_legitimate_interests_systems || []),
      ]),
    };
    onSave(allIds);
  };
  const handleRejectAll = () => {
    const emptyIds: EnabledIds = {
      purposesConsent: [],
      purposesLegint: [],
      specialPurposes: [],
      features: [],
      specialFeatures: [],
      vendorsConsent: [],
      vendorsLegint: [],
    };
    onSave(emptyIds);
  };

  return (
    <ConsentButtons
      experienceConfig={experience.experience_config}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={handleAcceptAll}
      onRejectAll={handleRejectAll}
      firstButton={firstButton}
    />
  );
};
