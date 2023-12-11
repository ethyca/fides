import { VNode, h } from "preact";

import { ConsentMethod, PrivacyExperience } from "../../lib/consent-types";
import { ConsentButtons } from "../ConsentButtons";
import type { EnabledIds, TcfModels } from "../../lib/tcf/types";

interface TcfConsentButtonProps {
  experience: PrivacyExperience;
  onManagePreferencesClick?: () => void;
  onSave: (consentMethod: ConsentMethod, keys: EnabledIds) => void;
  firstButton?: VNode;
  isMobile: boolean;
  includePrivacyPolicy?: boolean;
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
  isMobile,
  includePrivacyPolicy,
}: TcfConsentButtonProps) => {
  if (!experience.experience_config) {
    return null;
  }

  const handleAcceptAll = () => {
    const allIds: EnabledIds = {
      purposesConsent: getAllIds(experience.tcf_purpose_consents),
      purposesLegint: getAllIds(experience.tcf_purpose_legitimate_interests),
      specialPurposes: getAllIds(experience.tcf_special_purposes),
      features: getAllIds(experience.tcf_features),
      specialFeatures: getAllIds(experience.tcf_special_features),
      vendorsConsent: getAllIds([
        ...(experience.tcf_vendor_consents || []),
        ...(experience.tcf_system_consents || []),
      ]),
      vendorsLegint: getAllIds([
        ...(experience.tcf_vendor_legitimate_interests || []),
        ...(experience.tcf_system_legitimate_interests || []),
      ]),
    };
    onSave(ConsentMethod.accept, allIds);
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
    onSave(ConsentMethod.reject, emptyIds);
  };

  return (
    <ConsentButtons
      experienceConfig={experience.experience_config}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={handleAcceptAll}
      onRejectAll={handleRejectAll}
      firstButton={firstButton}
      isMobile={isMobile}
      includePrivacyPolicy={includePrivacyPolicy}
    />
  );
};
