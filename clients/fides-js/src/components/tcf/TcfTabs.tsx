import { h } from "preact";
import { useRef } from "preact/hooks";
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
  onChange: (payload: UpdateEnabledIds) => void;
  activeTabIndex: number;
  onTabChange: (tabIndex: number) => void;
}) => {
  const tcfTabs = [
    {
      name: "Purposes",
      content: (
        <div>
          <InfoBox>
            You can review and and exercise your right to consent to specific
            purposes by using the filter to switch between Consent and
            Legitimate Interest below.
          </InfoBox>
          <TcfPurposes
            allPurposesConsent={experience.tcf_consent_purposes}
            allPurposesLegint={experience.tcf_legitimate_interests_purposes}
            allSpecialPurposes={experience.tcf_special_purposes}
            enabledPurposeConsentIds={enabledIds.purposesConsent}
            enabledPurposeLegintIds={enabledIds.purposesLegint}
            enabledSpecialPurposeIds={enabledIds.specialPurposes}
            onChange={onChange}
          />
        </div>
      ),
    },
    {
      name: "Features",
      content: (
        <div>
          <InfoBox>
            You can review the list of features and exercise your right to
            consent to special features below.
          </InfoBox>
          <TcfFeatures
            allFeatures={experience.tcf_features}
            allSpecialFeatures={experience.tcf_special_features}
            enabledFeatureIds={enabledIds.features}
            enabledSpecialFeatureIds={enabledIds.specialFeatures}
            onChange={onChange}
          />
        </div>
      ),
    },
    {
      name: "Vendors",
      content: (
        <div>
          <InfoBox>
            You may review the list of vendors and the purposes or features of
            processing they individually declare below. You have the right to
            exercise you consent for each vendor based on the legal basis they
            assert.
          </InfoBox>
          <TcfVendors
            experience={experience}
            enabledVendorConsentIds={enabledIds.vendorsConsent}
            enabledVendorLegintIds={enabledIds.vendorsLegint}
            onChange={onChange}
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
