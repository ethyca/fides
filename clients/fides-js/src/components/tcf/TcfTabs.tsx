import { h } from "preact";
import { useCallback, useRef } from "preact/hooks";
import TcfPurposes from "./TcfPurposes";
import { PrivacyExperience } from "../../lib/consent-types";
import type { UpdateEnabledIds } from "./TcfOverlay";
import TcfFeatures from "./TcfFeatures";
import TcfVendors from "./TcfVendors";
import InfoBox from "../InfoBox";
import { EnabledIds } from "../../lib/tcf/types";

const KEY_ARROW_RIGHT = "ArrowRight";
const KEY_ARROW_LEFT = "ArrowLeft";

const TcfTabs = ({
  experience,
  enabledIds,
  onChange,
  activeTabIndex,
  onTabChange,
}: {
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
      name: "Purposes",
      content: (
        <div>
          <InfoBox>
            Below, you will find a list of the purposes and special features for
            which your data is being processed. You may exercise your rights for
            specific purposes, based on consent or legitimate interest, using
            the toggles below.
          </InfoBox>
          <TcfPurposes
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
      name: "Features",
      content: (
        <div>
          <InfoBox>
            Below, you will find a list of the features for which your data is
            being processed. You may exercise your rights for special features
            using the toggles below.
          </InfoBox>
          <TcfFeatures
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
      name: "Vendors",
      content: (
        <div>
          <InfoBox>
            Below, you will find a list of vendors processing your data and the
            purposes or features of processing they declare. You may exercise
            your rights for each vendor based on the legal basis they assert.
          </InfoBox>
          <TcfVendors
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
        {tcfTabs.map(({ name }, idx) => (
          <li role="presentation" key={name}>
            <button
              id={`fides-tab-${name}`}
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
        {tcfTabs.map(({ name, content }, idx) => (
          <section
            role="tabpanel"
            id={`fides-panel-${name}`}
            aria-labelledby={`fides-tab-${name}`}
            tabIndex={-1}
            hidden={idx !== activeTabIndex}
            key={name}
          >
            {content}
          </section>
        ))}
      </div>
    </div>
  );
};
export default TcfTabs;
