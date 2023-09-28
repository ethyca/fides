import { h } from "preact";
import { useRef } from "preact/hooks";
import TcfPurposes from "./TcfPurposes";
import { PrivacyExperience } from "../../lib/consent-types";
import type { EnabledIds, UpdateEnabledIds } from "./TcfOverlay";
import TcfFeatures from "./TcfFeatures";
import TcfVendors from "./TcfVendors";
import InfoBox from "../InfoBox";

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
          <InfoBox title="Transparency & Consent Framework">
            The purposes for which your personal data is being collected are
            detailed here. You can choose to opt in or opt out of any of these
            purposes.
          </InfoBox>
          <TcfPurposes
            allPurposes={experience.tcf_purposes}
            allSpecialPurposes={experience.tcf_special_purposes}
            enabledPurposeIds={enabledIds.purposes}
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
          <InfoBox title="Transparency & Consent Framework">
            The features for which your personal data is being collected are
            detailed here. You can choose to opt in or opt out of any of these
            purposes.
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
          <InfoBox title="Transparency & Consent Framework">
            The features for which your personal data is being collected are
            detailed here. You can choose to opt in or opt out of any of these
            purposes.
          </InfoBox>
          <TcfVendors
            vendors={[
              ...(experience.tcf_vendors || []),
              ...(experience.tcf_systems || []),
            ]}
            enabledVendorConsentIds={enabledIds.vendorsConsent}
            enabledVendorLegintIds={enabledIds.vendorsLegint}
            onChange={onChange}
            gvl={experience.gvl}
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
