import { h } from "preact";

import { TCFFeatureRecord, TCFSpecialFeatureRecord } from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import type { UpdateEnabledIds } from "./TcfOverlay";
import RecordsList from "./RecordsList";
import EmbeddedVendorList from "./EmbeddedVendorList";

const FeatureChildren = ({ feature }: { feature: TCFFeatureRecord }) => {
  const vendors = [...(feature.vendors || []), ...(feature.systems || [])];
  return (
    <div>
      <p className="fides-tcf-toggle-content">{feature.description}</p>
      <EmbeddedVendorList vendors={vendors} />
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
    <RecordsList<TCFFeatureRecord>
      title="Features"
      items={allFeatures ?? []}
      enabledIds={enabledFeatureIds}
      onToggle={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "features" })
      }
      renderToggleChild={(f) => <FeatureChildren feature={f} />}
      hideToggles
    />
    <RecordsList<TCFSpecialFeatureRecord>
      title="Special features"
      items={allSpecialFeatures ?? []}
      enabledIds={enabledSpecialFeatureIds}
      onToggle={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "specialFeatures" })
      }
      renderToggleChild={(f) => <FeatureChildren feature={f} />}
    />
  </div>
);

export default TcfFeatures;
