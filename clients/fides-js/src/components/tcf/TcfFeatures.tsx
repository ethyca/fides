import { h } from "preact";

import { PrivacyExperience } from "../../lib/consent-types";
import { FidesServingToggleDetails } from "../../lib/events";
import { useI18n } from "../../lib/i18n/i18n-context";
import { TCFFeatureRecord, TCFSpecialFeatureRecord } from "../../lib/tcf/types";
import EmbeddedVendorList from "./EmbeddedVendorList";
import RecordsList, { RecordListType } from "./RecordsList";
import { UpdateEnabledIds } from "./TcfTabs";

const FeatureChildren = ({
  type,
  feature,
}: {
  type: RecordListType;
  feature: TCFFeatureRecord;
}) => {
  const { i18n } = useI18n();
  const vendors = [...(feature.vendors || []), ...(feature.systems || [])];
  return (
    <div>
      <p className="fides-tcf-toggle-content">
        {i18n.t(`exp.tcf.${type}.${feature.id}.description`)}
      </p>
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
  onChange: (
    payload: UpdateEnabledIds,
    toggleDetails: FidesServingToggleDetails,
  ) => void;
}) => {
  const { i18n } = useI18n();
  return (
    <div>
      <RecordsList<TCFFeatureRecord>
        type="features"
        title={i18n.t("static.tcf.features")}
        items={allFeatures ?? []}
        enabledIds={enabledFeatureIds}
        onToggle={(newEnabledIds, _, toggleDetails) =>
          onChange({ newEnabledIds, modelType: "features" }, toggleDetails)
        }
        renderToggleChild={(f) => (
          <FeatureChildren type="features" feature={f} />
        )}
        hideToggles
      />
      <RecordsList<TCFSpecialFeatureRecord>
        type="specialFeatures"
        title={i18n.t("static.tcf.special_features")}
        items={allSpecialFeatures ?? []}
        enabledIds={enabledSpecialFeatureIds}
        onToggle={(newEnabledIds, _, toggleDetails) =>
          onChange(
            { newEnabledIds, modelType: "specialFeatures" },
            toggleDetails,
          )
        }
        renderToggleChild={(f) => (
          <FeatureChildren type="specialFeatures" feature={f} />
        )}
      />
    </div>
  );
};

export default TcfFeatures;
