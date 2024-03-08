import { h } from "preact";

import { PrivacyExperience } from "../../lib/consent-types";
import { I18n } from "../../lib/i18n";
import { TCFFeatureRecord, TCFSpecialFeatureRecord } from "../../lib/tcf/types";
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

// static.tcf.features
// static.tcf.special_features
const TcfFeatures = ({
  i18n,
  allFeatures,
  allSpecialFeatures,
  enabledFeatureIds,
  enabledSpecialFeatureIds,
  onChange,
}: {
  i18n: I18n;
  allFeatures: PrivacyExperience["tcf_features"];
  allSpecialFeatures: PrivacyExperience["tcf_special_features"];
  enabledFeatureIds: string[];
  enabledSpecialFeatureIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => (
  <div>
    <RecordsList<TCFFeatureRecord>
      i18n={i18n}
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
      i18n={i18n}
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
