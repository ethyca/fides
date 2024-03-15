import { h } from "preact";
import { useCallback, useRef } from "preact/hooks";
import { I18n } from "../../lib/i18n";
import { PrivacyExperience } from "../../lib/consent-types";
import { EnabledIds } from "../../lib/tcf/types";
import TcfPurposes from "./TcfPurposes";
import type { UpdateEnabledIds } from "./TcfOverlay";
import TcfFeatures from "./TcfFeatures";
import TcfVendors from "./TcfVendors";
import InfoBox from "../InfoBox";

const KEY_ARROW_RIGHT = "ArrowRight";
const KEY_ARROW_LEFT = "ArrowLeft";

const TcfTabs = ({
  i18n,
  experience,
  enabledIds,
  onChange,
  activeTabIndex,
  onTabChange,
}: {
  i18n: I18n;
  experience: PrivacyExperience;
  enabledIds: EnabledIds;
  onChange: (payload: EnabledIds) => void;
  activeTabIndex: number;
  onTabChange: (tabIndex: number) => void;
}) => {
  const handleUpdateDraftState = useCallback(
    ({ newEnabledIds, modelType }: UpdateEnabledIds) => {
      const updated = { ...enabledIds, [modelType]: newEnabledIds };
      onChange(updated);
    },
    [enabledIds, onChange]
  );

  const tcfTabs = [
    {
      name: i18n.t("static.tcf.purposes"),
      type: "purposes",
      content: (
        <div>
          <InfoBox>{i18n.t("static.tcf.purposes.description")}</InfoBox>
          <TcfPurposes
            i18n={i18n}
            allPurposesConsent={experience.tcf_purpose_consents}
            allPurposesLegint={experience.tcf_purpose_legitimate_interests}
            allSpecialPurposes={experience.tcf_special_purposes}
            enabledPurposeConsentIds={enabledIds.purposesConsent}
            enabledPurposeLegintIds={enabledIds.purposesLegint}
            enabledSpecialPurposeIds={enabledIds.specialPurposes}
            onChange={handleUpdateDraftState}
          />
        </div>
      ),
    },
    {
      name: i18n.t("static.tcf.features"),
      type: "features",
      content: (
        <div>
          <InfoBox>{i18n.t("static.tcf.features.description")}</InfoBox>
          <TcfFeatures
            i18n={i18n}
            allFeatures={experience.tcf_features}
            allSpecialFeatures={experience.tcf_special_features}
            enabledFeatureIds={enabledIds.features}
            enabledSpecialFeatureIds={enabledIds.specialFeatures}
            onChange={handleUpdateDraftState}
          />
        </div>
      ),
    },
    {
      name: i18n.t("static.tcf.vendors"),
      type: "vendors",
      content: (
        <div>
          <InfoBox>{i18n.t("static.tcf.vendors.description")}</InfoBox>
          <TcfVendors
            i18n={i18n}
            experience={experience}
            enabledVendorConsentIds={enabledIds.vendorsConsent}
            enabledVendorLegintIds={enabledIds.vendorsLegint}
            onChange={handleUpdateDraftState}
          />
        </div>
      ),
    },
  ];

  const inputRefs = [
    useRef<HTMLButtonElement>(null),
    useRef<HTMLButtonElement>(null),
    useRef<HTMLButtonElement>(null),
  ];
  const handleKeyDown = (event: KeyboardEvent) => {
    let newActiveTab;
    if (event.code === KEY_ARROW_RIGHT) {
      event.preventDefault();
      newActiveTab =
        activeTabIndex === tcfTabs.length - 1 ? 0 : activeTabIndex + 1;
    }
    if (event.code === KEY_ARROW_LEFT) {
      event.preventDefault();
      newActiveTab =
        activeTabIndex === 0 ? tcfTabs.length - 1 : activeTabIndex - 1;
    }
    if (newActiveTab != null) {
      onTabChange(newActiveTab);
      inputRefs[newActiveTab].current?.focus();
    }
  };
  return (
    <div className="fides-tabs">
      <ul role="tablist" className="fides-tab-list">
        {tcfTabs.map(({ name, type }, idx) => (
          <li role="presentation" key={type}>
            <button
              id={`fides-tab-${type}`}
              aria-selected={idx === activeTabIndex}
              onClick={() => {
                onTabChange(idx);
              }}
              role="tab"
              type="button"
              className="fides-tab-button"
              tabIndex={idx === activeTabIndex ? undefined : -1}
              onKeyDown={handleKeyDown}
              ref={inputRefs[idx]}
            >
              {name}
            </button>
          </li>
        ))}
      </ul>
      <div className="tabpanel-container">
        {tcfTabs.map(({ type, content }, idx) => (
          <section
            role="tabpanel"
            id={`fides-panel-${type}`}
            aria-labelledby={`fides-tab-${type}`}
            tabIndex={-1}
            hidden={idx !== activeTabIndex}
            key={type}
          >
            {content}
          </section>
        ))}
      </div>
    </div>
  );
};
export default TcfTabs;
