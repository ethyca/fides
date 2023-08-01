import { h } from "preact";

import { TCFFeatureRecord } from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import type { UpdateEnabledIds } from "./TcfOverlay";
import DataUseToggle from "../DataUseToggle";

const FeatureBlock = ({
  label,
  allFeatures,
  enabledIds,
  onChange,
}: {
  label: string;
  allFeatures: TCFFeatureRecord[] | undefined;
  enabledIds: string[];
  onChange: (newIds: string[]) => void;
}) => {
  if (!allFeatures || allFeatures.length === 0) {
    return null;
  }

  const allChecked = allFeatures.length === enabledIds.length;
  const handleToggle = (feature: TCFFeatureRecord) => {
    const featureId = `${feature.id}`;
    if (enabledIds.indexOf(featureId) !== -1) {
      onChange(enabledIds.filter((e) => e !== featureId));
    } else {
      onChange([...enabledIds, featureId]);
    }
  };
  const handleToggleAll = () => {
    if (allChecked) {
      onChange([]);
    } else {
      onChange(allFeatures.map((f) => `${f.id}`));
    }
  };

  return (
    <div>
      <DataUseToggle
        dataUse={{ key: label, name: label }}
        onToggle={handleToggleAll}
        checked={allChecked}
        isHeader
      />
      {allFeatures.map((f) => (
        <DataUseToggle
          dataUse={{ key: `${f.id}`, name: f.name }}
          onToggle={() => {
            handleToggle(f);
          }}
          checked={enabledIds.indexOf(`${f.id}`) !== -1}
        />
      ))}
    </div>
  );
};

const TcfFeatures = ({
  allFeatures,
  allSpecialFeatures,
  enabledFeatureIds,
  enabledSpecialFeatureIds,
  onChange,
}: {
  allFeatures: PrivacyExperience["tcf_features"];
  allSpecialFeatures: PrivacyExperience["tcf_special_features"];
  enabledFeatureIds: string[];
  enabledSpecialFeatureIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => (
  <div>
    <FeatureBlock
      label="Features"
      allFeatures={allFeatures}
      enabledIds={enabledFeatureIds}
      onChange={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "features" })
      }
    />
    <FeatureBlock
      label="Special features"
      allFeatures={allSpecialFeatures}
      enabledIds={enabledSpecialFeatureIds}
      onChange={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "specialFeatures" })
      }
    />
  </div>
);

export default TcfFeatures;
