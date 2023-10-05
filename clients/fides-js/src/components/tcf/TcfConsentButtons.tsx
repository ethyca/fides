import { ComponentChildren, VNode, h } from "preact";

import { PrivacyExperience } from "../../lib/consent-types";
import { ConsentButtons } from "../ConsentButtons";
import type { EnabledIds } from "../../lib/tcf/types";
import {
  TCFPurposeRecord,
  TCFFeatureRecord,
  TCFVendorRecord,
} from "../../lib/tcf/types";

interface TcfConsentButtonProps {
  experience: PrivacyExperience;
  onManagePreferencesClick?: () => void;
  onSave: (keys: EnabledIds) => void;
  firstButton?: VNode;
  children?: ComponentChildren;
}

const getAllIds = (
  modelList:
    | TCFPurposeRecord[]
    | TCFFeatureRecord[]
    | TCFVendorRecord[]
    | undefined
) => {
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
  children,
}: TcfConsentButtonProps) => {
  if (!experience.experience_config) {
    return null;
  }

  const handleAcceptAll = () => {
    const vendorsAndSystems = [
      ...(experience.tcf_vendors || []),
      ...(experience.tcf_systems || []),
    ];
    const allIds: EnabledIds = {
      purposes: getAllIds(experience.tcf_purposes),
      specialPurposes: getAllIds(experience.tcf_special_purposes),
      features: getAllIds(experience.tcf_features),
      specialFeatures: getAllIds(experience.tcf_special_features),
      // TODO: make these read from separate fields once the backend supports it (fidesplus1128)
      vendorsConsent: getAllIds(vendorsAndSystems),
      vendorsLegint: getAllIds(vendorsAndSystems),
    };
    onSave(allIds);
  };
  const handleRejectAll = () => {
    const emptyIds: EnabledIds = {
      purposes: [],
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
    >
      {children}
    </ConsentButtons>
  );
};
