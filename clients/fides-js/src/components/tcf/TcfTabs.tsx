import { useCallback, useRef } from "preact/hooks";

import {
  PrivacyExperience,
  PrivacyExperienceMinimal,
} from "../../lib/consent-types";
import { FidesEventDetailsPreference } from "../../lib/events";
import { useI18n } from "../../lib/i18n/i18n-context";
import { PAGE_SIZE } from "../../lib/paging";
import {
  EnabledIds,
  PrivacyNoticeWithBestTranslation,
} from "../../lib/tcf/types";
import InfoBox from "../InfoBox";
import { RecordsListSkeletons } from "./RecordsListSkeletons";
import TcfFeatures from "./TcfFeatures";
import TcfPurposes from "./TcfPurposes";
import TcfVendors from "./TcfVendors";

const KEY_ARROW_RIGHT = "ArrowRight";
const KEY_ARROW_LEFT = "ArrowLeft";

export interface UpdateEnabledIds {
  newEnabledIds: string[];
  modelType: keyof EnabledIds;
}

const TcfTabs = ({
  experience,
  customNotices,
  enabledIds,
  onChange,
  activeTabIndex,
  onTabChange,
}: {
  experience: PrivacyExperience | PrivacyExperienceMinimal;
  customNotices: PrivacyNoticeWithBestTranslation[] | undefined;
  enabledIds: EnabledIds;
  onChange: (
    payload: EnabledIds,
    preferenceDetails: FidesEventDetailsPreference,
  ) => void;
  activeTabIndex: number;
  onTabChange: (tabIndex: number) => void;
}) => {
  const { i18n } = useI18n();
  const handleUpdateDraftState = useCallback(
    (
      { newEnabledIds, modelType }: UpdateEnabledIds,
      preferenceDetails: FidesEventDetailsPreference,
    ) => {
      const updated = { ...enabledIds, [modelType]: newEnabledIds };
      onChange(updated, preferenceDetails);
    },
    [enabledIds, onChange],
  );

  const tcfTabs = [
    {
      name: i18n.t("static.tcf.purposes"),
      type: "purposes",
      content: (
        <div>
          <InfoBox>{i18n.t("static.tcf.purposes.description")}</InfoBox>
          {experience.minimal_tcf ? (
            <RecordsListSkeletons
              rows={
                ((experience as PrivacyExperienceMinimal)
                  .tcf_purpose_consent_ids?.length ?? 0) +
                (customNotices?.length ?? 0)
              }
            />
          ) : (
            <TcfPurposes
              allPurposesConsent={
                (experience as PrivacyExperience).tcf_purpose_consents
              }
              allCustomPurposesConsent={customNotices}
              allPurposesLegint={
                (experience as PrivacyExperience)
                  .tcf_purpose_legitimate_interests
              }
              allSpecialPurposes={
                (experience as PrivacyExperience).tcf_special_purposes
              }
              enabledIds={enabledIds}
              onChange={handleUpdateDraftState}
            />
          )}
        </div>
      ),
    },
    {
      name: i18n.t("static.tcf.features"),
      type: "features",
      content: (
        <div>
          <InfoBox>{i18n.t("static.tcf.features.description")}</InfoBox>
          {experience.minimal_tcf ? (
            <RecordsListSkeletons
              rows={
                ((experience as PrivacyExperienceMinimal).tcf_feature_ids
                  ?.length ?? 0) +
                ((experience as PrivacyExperienceMinimal)
                  .tcf_special_feature_ids?.length ?? 0)
              }
            />
          ) : (
            <TcfFeatures
              allFeatures={(experience as PrivacyExperience).tcf_features}
              allSpecialFeatures={
                (experience as PrivacyExperience).tcf_special_features
              }
              enabledIds={enabledIds}
              onChange={handleUpdateDraftState}
            />
          )}
        </div>
      ),
    },
    {
      name: i18n.t("static.tcf.vendors"),
      type: "vendors",
      content: (
        <div>
          <InfoBox>{i18n.t("static.tcf.vendors.description")}</InfoBox>
          {experience.minimal_tcf ? (
            <RecordsListSkeletons
              rows={Math.min(
                (experience as PrivacyExperienceMinimal).tcf_vendor_consent_ids
                  ?.length ?? 0,
                PAGE_SIZE,
              )}
            />
          ) : (
            <TcfVendors
              experience={experience as PrivacyExperience}
              enabledIds={enabledIds}
              onChange={handleUpdateDraftState}
            />
          )}
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
