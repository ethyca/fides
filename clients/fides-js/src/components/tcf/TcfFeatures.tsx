import { h } from "preact";

import { UpdateEnabledIds } from "~/components/tcf/TcfTabs";

import { PrivacyExperience } from "../../lib/consent-types";
import { I18n } from "../../lib/i18n";
import { TCFFeatureRecord, TCFSpecialFeatureRecord } from "../../lib/tcf/types";
import EmbeddedVendorList from "./EmbeddedVendorList";
import RecordsList, { RecordListType } from "./RecordsList";

const FeatureChildren = ({
  i18n,
  type,
  feature,
}: {
  i18n: I18n;
  type: RecordListType;
  feature: TCFFeatureRecord;
}) => {
  const vendors = [...(feature.vendors || []), ...(feature.systems || [])];
  return (
    <div>
      <p className="fides-tcf-toggle-content">
        {i18n.t(`exp.tcf.${type}.${feature.id}.description`)}
      </p>
      <EmbeddedVendorList i18n={i18n} vendors={vendors} />
    </div>
  );
};

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
      type="features"
      title={i18n.t("static.tcf.features")}
      items={allFeatures ?? []}
      enabledIds={enabledFeatureIds}
      onToggle={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "features" })
      }
      renderToggleChild={(f) => (
        <FeatureChildren i18n={i18n} type="features" feature={f} />
      )}
      hideToggles
    />
    <RecordsList<TCFSpecialFeatureRecord>
      i18n={i18n}
      type="specialFeatures"
      title={i18n.t("static.tcf.special_features")}
      items={allSpecialFeatures ?? []}
      enabledIds={enabledSpecialFeatureIds}
      onToggle={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "specialFeatures" })
      }
      renderToggleChild={(f) => (
        <FeatureChildren i18n={i18n} type="specialFeatures" feature={f} />
      )}
    />
  </div>
);

export default TcfFeatures;
