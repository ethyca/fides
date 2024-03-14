import { VNode, h } from "preact";

import { ConsentMethod, PrivacyExperience } from "../../lib/consent-types";
import { ConsentButtons } from "../ConsentButtons";
import type { EnabledIds, TcfModels } from "../../lib/tcf/types";
import { I18n } from "../../lib/i18n";

interface TcfConsentButtonProps {
  experience: PrivacyExperience;
  i18n: I18n;
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
  i18n,
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
    onSave(ConsentMethod.ACCEPT, allIds);
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
    onSave(ConsentMethod.REJECT, emptyIds);
  };

  return (
    <ConsentButtons
      i18n={i18n}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={handleAcceptAll}
      onRejectAll={handleRejectAll}
      firstButton={firstButton}
      isMobile={isMobile}
      includePrivacyPolicy={includePrivacyPolicy}
    />
  );
};
