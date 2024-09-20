import { h, VNode } from "preact";

import {
  ConsentMethod,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyExperienceMinimal,
} from "../../lib/consent-types";
import type { EnabledIds, TcfModels } from "../../lib/tcf/types";
import { ConsentButtons } from "../ConsentButtons";

interface TcfConsentButtonProps {
  experience: PrivacyExperience | PrivacyExperienceMinimal;
  options: FidesInitOptions;
  onManagePreferencesClick?: () => void;
  onSave: (consentMethod: ConsentMethod, keys: EnabledIds) => void;
  renderFirstButton?: () => VNode;
  isInModal?: boolean;
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
  renderFirstButton,
  isInModal,
  options,
}: TcfConsentButtonProps) => {
  if (!experience.experience_config) {
    return null;
  }

  const isGVLLoading = Object.keys(experience.gvl || {}).length === 0;

  const handleAcceptAll = () => {
    let allIds: EnabledIds;
    if (!experience.minimal_tcf) {
      // eslint-disable-next-line no-param-reassign
      experience = experience as PrivacyExperience;
      allIds = {
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
    } else {
      // eslint-disable-next-line no-param-reassign
      experience = experience as PrivacyExperienceMinimal;
      allIds = {
        purposesConsent:
          experience.tcf_purpose_consent_ids?.map((id) => `${id}`) || [],
        purposesLegint:
          experience.tcf_purpose_legitimate_interest_ids?.map(
            (id) => `${id}`,
          ) || [],
        specialPurposes:
          experience.tcf_special_purpose_ids?.map((id) => `${id}`) || [],
        features: experience.tcf_feature_ids?.map((id) => `${id}`) || [],
        specialFeatures:
          experience.tcf_special_feature_ids?.map((id) => `${id}`) || [],
        vendorsConsent: [
          ...(experience.tcf_vendor_consent_ids || []),
          ...(experience.tcf_system_consent_ids || []),
        ],
        vendorsLegint: [
          ...(experience.tcf_vendor_legitimate_interest_ids || []),
          ...(experience.tcf_system_legitimate_interest_ids || []),
        ],
      };
    }
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
      availableLocales={experience.available_locales}
      onManagePreferencesClick={onManagePreferencesClick}
      onAcceptAll={handleAcceptAll}
      onRejectAll={handleRejectAll}
      renderFirstButton={renderFirstButton}
      isInModal={isInModal}
      options={options}
      isTCF
      isMinimalTCF={experience.minimal_tcf}
      isGVLLoading={isGVLLoading}
    />
  );
};
