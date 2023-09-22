import { h } from "preact";

import { TCFFeatureRecord } from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import type { UpdateEnabledIds } from "./TcfOverlay";
import DataUseToggle from "../DataUseToggle";

const TcfFeatures = ({
  allSpecialFeatures,
  enabledSpecialFeatureIds,
  onChange,
}: {
  allSpecialFeatures: PrivacyExperience["tcf_special_features"];
  enabledSpecialFeatureIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => {
  const modelType = "specialFeatures";
  const label = "Special features";
  const handleChange = (newIds: string[]) => {
    onChange({ newEnabledIds: newIds, modelType });
  };
  if (!allSpecialFeatures || allSpecialFeatures.length === 0) {
    return null;
  }

  const allChecked =
    allSpecialFeatures.length === enabledSpecialFeatureIds.length;
  const handleToggle = (feature: TCFFeatureRecord) => {
    const featureId = `${feature.id}`;
    if (enabledSpecialFeatureIds.indexOf(featureId) !== -1) {
      handleChange(enabledSpecialFeatureIds.filter((e) => e !== featureId));
    } else {
      handleChange([...enabledSpecialFeatureIds, featureId]);
    }
  };
  const handleToggleAll = () => {
    if (allChecked) {
      handleChange([]);
    } else {
      handleChange(allSpecialFeatures.map((f) => `${f.id}`));
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
      {allSpecialFeatures.map((f) => {
        const vendors = [...(f.vendors || []), ...(f.systems || [])];
        return (
          <DataUseToggle
            dataUse={{ key: `${f.id}`, name: f.name }}
            onToggle={() => {
              handleToggle(f);
            }}
            checked={enabledSpecialFeatureIds.indexOf(`${f.id}`) !== -1}
          >
            <div>
              <p className="fides-tcf-toggle-content">{f.description}</p>
              {vendors.length ? (
                <p className="fides-tcf-toggle-content fides-background-dark fides-tcf-purpose-vendor">
                  <span className="fides-tcf-purpose-vendor-title">
                    Vendors we use for this feature
                  </span>
                  <ul className="fides-tcf-purpose-vendor-list">
                    {vendors.map((v) => (
                      <li>{v.name}</li>
                    ))}
                  </ul>
                </p>
              ) : null}
            </div>
          </DataUseToggle>
        );
      })}
    </div>
  );
};

export default TcfFeatures;
