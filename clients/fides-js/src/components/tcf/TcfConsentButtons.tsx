import { VNode, h } from "preact";

import { PrivacyExperience } from "../../lib/consent-types";
import { ConsentButtons } from "../ConsentButtons";
import type { EnabledIds } from "./TcfOverlay";
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
}: TcfConsentButtonProps) => {
  if (!experience.experience_config) {
    return null;
  }

  const handleAcceptAll = () => {
    const allIds: EnabledIds = {
      purposes: getAllIds(experience.tcf_purposes),
      specialPurposes: getAllIds(experience.tcf_special_purposes),
      features: getAllIds(experience.tcf_features),
      specialFeatures: getAllIds(experience.tcf_special_features),
      // TODO: separate these out once the backend can handle it
      vendorsConsent: getAllIds(experience.tcf_vendors),
      vendorsLegint: getAllIds(experience.tcf_vendors),
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
    />
  );
};
