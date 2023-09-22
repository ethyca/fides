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
      specialFeatures: getAllIds(experience.tcf_special_features),
      vendors: getAllIds(experience.tcf_vendors),
      systems: getAllIds(experience.tcf_systems),
    };
    onSave(allIds);
  };
  const handleRejectAll = () => {
    const emptyIds: EnabledIds = {
      purposes: [],
      specialFeatures: [],
      vendors: [],
      systems: [],
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
