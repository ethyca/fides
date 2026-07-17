import { PrivacyExperience } from "../../lib/consent-types";
import { FidesEventDetailsPreference } from "../../lib/events";
import { messageExists } from "../../lib/i18n";
import { useI18n } from "../../lib/i18n/i18n-context";
import {
  EnabledIds,
  TCFFeatureRecord,
  TCFSpecialFeatureRecord,
} from "../../lib/tcf/types";
import EmbeddedVendorList from "./EmbeddedVendorList";
import RecordsList, { RecordListType } from "./RecordsList";
import { UpdateEnabledIds } from "./TcfTabs";

const FeatureChildren = ({
  type,
  feature,
}: {
  type: RecordListType;
  feature: TCFFeatureRecord | TCFSpecialFeatureRecord;
}) => {
  const { i18n } = useI18n();
  const vendors = [...(feature.vendors || []), ...(feature.systems || [])];
  // The standard feature-explanation text and illustrations were introduced
  // with IAB TCF Policy v5.0.b / GVL specification version 4. They are rendered
  // only when present, mirroring how purpose illustrations are handled, so
  // older GVL specification versions render exactly as before.
  const standardTextKey = `exp.tcf.${type}.${feature.id}.standard_texts`;
  return (
    <div>
      <p className="fides-tcf-toggle-content">
        {i18n.t(`exp.tcf.${type}.${feature.id}.description`)}
      </p>
      {(feature.illustrations || []).map((illustration, i) => (
        <p
          key={illustration}
          className="fides-tcf-illustration fides-background-dark"
        >
          {i18n.t(`exp.tcf.${type}.${feature.id}.illustrations.${i}`)}
        </p>
      ))}
      {messageExists(i18n, standardTextKey) && (
        <p className="fides-tcf-toggle-content">{i18n.t(standardTextKey)}</p>
      )}
      <EmbeddedVendorList vendors={vendors} />
    </div>
  );
};

const TcfFeatures = ({
  allFeatures,
  allSpecialFeatures,
  enabledIds,
  onChange,
}: {
  allFeatures: PrivacyExperience["tcf_features"];
  allSpecialFeatures: PrivacyExperience["tcf_special_features"];
  enabledIds: EnabledIds;
  onChange: (
    payload: UpdateEnabledIds,
    preferenceDetails: FidesEventDetailsPreference,
  ) => void;
}) => {
  const { i18n } = useI18n();
  const {
    features: enabledFeatureIds,
    specialFeatures: enabledSpecialFeatureIds,
  } = enabledIds;
  return (
    <div>
      <RecordsList<TCFFeatureRecord>
        type="features"
        title={i18n.t("static.tcf.features")}
        items={allFeatures ?? []}
        enabledIds={enabledFeatureIds}
        onToggle={() => {
          // Regular features cannot be toggled - they are notice-only.
          // The hideToggles prop ensures the UI doesn't show toggle controls,
          // and this no-op handler ensures no events are fired even if somehow triggered.
        }}
        renderDropdownChild={(f) => (
          <FeatureChildren type="features" feature={f} />
        )}
        hideToggles
      />
      <RecordsList<TCFSpecialFeatureRecord>
        type="specialFeatures"
        title={i18n.t("static.tcf.special_features")}
        items={allSpecialFeatures ?? []}
        enabledIds={enabledSpecialFeatureIds}
        onToggle={(newEnabledIds, item) =>
          onChange(
            { newEnabledIds, modelType: "specialFeatures" },
            {
              key: `tcf_special_feature_${item.id}`,
              type: "tcf_special_feature",
            },
          )
        }
        renderDropdownChild={(f) => (
          <FeatureChildren type="specialFeatures" feature={f} />
        )}
      />
    </div>
  );
};

export default TcfFeatures;
