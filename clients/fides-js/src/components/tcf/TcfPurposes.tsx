import { h } from "preact";
import { useMemo, useState } from "preact/hooks";

import { UpdateEnabledIds } from "~/components/tcf/TcfTabs";

import { ConsentMechanism, PrivacyExperience } from "../../lib/consent-types";
import {
  FidesEventDetailsPreference,
  FidesEventDetailsTrigger,
} from "../../lib/events";
import { useI18n } from "../../lib/i18n/i18n-context";
import { LEGAL_BASIS_OPTIONS } from "../../lib/tcf/constants";
import { getUniquePurposeRecords, hasLegalBasis } from "../../lib/tcf/purposes";
import {
  EnabledIds,
  LegalBasisEnum,
  PrivacyNoticeWithBestTranslation,
  PurposeRecord,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFSpecialPurposeRecord,
} from "../../lib/tcf/types";
import EmbeddedVendorList from "./EmbeddedVendorList";
import RadioGroup from "./RadioGroup";
import RecordsList, { RecordListItem, RecordListType } from "./RecordsList";

type TCFPurposeRecord =
  | TCFPurposeConsentRecord
  | TCFPurposeLegitimateInterestsRecord
  | PrivacyNoticeWithBestTranslation;

const PurposeDetails = ({
  type,
  purpose,
  isCustomPurpose = false,
}: {
  type: RecordListType;
  purpose: TCFPurposeRecord;
  isCustomPurpose?: boolean;
}) => {
  const { i18n } = useI18n();
  if (isCustomPurpose) {
    // eslint-disable-next-line no-param-reassign
    purpose = purpose as PrivacyNoticeWithBestTranslation;
    // Custom purposes already have translation details
    return (
      <div>
        <p className="fides-tcf-toggle-content">
          {purpose.bestTranslation?.description}
        </p>
      </div>
    );
  }
  // eslint-disable-next-line no-param-reassign
  purpose = purpose as
    | TCFPurposeConsentRecord
    | TCFPurposeLegitimateInterestsRecord;
  const vendors = [...(purpose.vendors || []), ...(purpose.systems || [])];
  return (
    <div>
      <p className="fides-tcf-toggle-content">
        {i18n.t(`exp.tcf.${type}.${purpose.id}.description`)}
      </p>
      {purpose.illustrations.map((illustration: any, i: any) => (
        <p
          key={illustration}
          className="fides-tcf-illustration fides-background-dark"
        >
          {i18n.t(`exp.tcf.${type}.${purpose.id}.illustrations.${i}`)}
        </p>
      ))}

      <EmbeddedVendorList vendors={vendors} />
    </div>
  );
};

const TcfPurposes = ({
  allPurposesConsent = [],
  allCustomPurposesConsent = [],
  allPurposesLegint = [],
  allSpecialPurposes,
  enabledPurposeConsentIds,
  enabledCustomPurposeConsentIds,
  enabledPurposeLegintIds,
  enabledSpecialPurposeIds,
  onChange,
}: {
  allPurposesConsent: TCFPurposeConsentRecord[] | undefined;
  allCustomPurposesConsent: Array<PrivacyNoticeWithBestTranslation> | undefined;
  enabledPurposeConsentIds: string[];
  allSpecialPurposes: PrivacyExperience["tcf_special_purposes"];
  allPurposesLegint: TCFPurposeLegitimateInterestsRecord[] | undefined;
  enabledPurposeLegintIds: string[];
  enabledCustomPurposeConsentIds: string[];
  enabledSpecialPurposeIds: string[];
  onChange: (
    payload: UpdateEnabledIds,
    eventTrigger: FidesEventDetailsTrigger,
    preference: FidesEventDetailsPreference,
  ) => void;
}) => {
  const { i18n } = useI18n();
  const { uniquePurposes } = useMemo(
    () =>
      getUniquePurposeRecords({
        consentPurposes: allPurposesConsent,
        legintPurposes: allPurposesLegint,
      }),
    [allPurposesConsent, allPurposesLegint],
  );

  const [activeLegalBasisOption, setActiveLegalBasisOption] = useState(
    LEGAL_BASIS_OPTIONS[0],
  );

  const activeData: {
    purposes: PurposeRecord[];
    customPurposes?: PrivacyNoticeWithBestTranslation[];
    purposeModelType: keyof EnabledIds;
    enabledPurposeIds: string[];
    enabledCustomPurposeIds?: string[];
    specialPurposes: TCFSpecialPurposeRecord[];
    enabledSpecialPurposeIds: string[];
  } = useMemo(() => {
    const specialPurposes = allSpecialPurposes ?? [];
    if (activeLegalBasisOption.value === LegalBasisEnum.CONSENT.toString()) {
      return {
        purposes: uniquePurposes.filter((p) => p.isConsent),
        customPurposes: allCustomPurposesConsent.map((purpose) => ({
          ...purpose,
          disabled: purpose.consent_mechanism === ConsentMechanism.NOTICE_ONLY,
        })), // all custom purposes are "consent" purposes
        purposeModelType: "purposesConsent",
        enabledPurposeIds: enabledPurposeConsentIds,
        enabledCustomPurposeIds: enabledCustomPurposeConsentIds,
        specialPurposes: specialPurposes.filter((sp) =>
          hasLegalBasis(sp, LegalBasisEnum.CONSENT),
        ),
        enabledSpecialPurposeIds,
      };
    }
    return {
      purposes: uniquePurposes.filter((p) => p.isLegint),
      purposeModelType: "purposesLegint",
      enabledPurposeIds: enabledPurposeLegintIds,
      specialPurposes: specialPurposes.filter((sp) =>
        hasLegalBasis(sp, LegalBasisEnum.LEGITIMATE_INTERESTS),
      ),
      enabledSpecialPurposeIds,
    };
  }, [
    allSpecialPurposes,
    activeLegalBasisOption,
    uniquePurposes,
    enabledPurposeLegintIds,
    enabledSpecialPurposeIds,
    allCustomPurposesConsent,
    enabledPurposeConsentIds,
    enabledCustomPurposeConsentIds,
  ]);

  /**
   * Handles toggling of purposes and special purposes in the TCF interface.
   *
   * Takes a modelType (e.g., purposesConsent, specialPurposes) that determines how
   * the change will be persisted, a list of newly enabled IDs, the purpose/notice
   * being toggled (which can be a standard TCF purpose, custom privacy notice, or
   * special purpose), and details about what triggered the toggle.
   */
  const handleToggle = (
    modelType: keyof EnabledIds,
    newEnabledIds: string[],
    item:
      | PurposeRecord
      | PrivacyNoticeWithBestTranslation
      | TCFSpecialPurposeRecord,
    eventTrigger: FidesEventDetailsTrigger,
  ) => {
    // Determine the preference being changed based on the model type:
    // - customPurposesConsent -> notice
    // - purposesConsent -> tcf_purpose_consent
    // - purposesLegint/specialPurposes -> tcf_purpose_legitimate_interest
    //
    // NOTE: TCF purposes don't have equivalent notice "keys" today, but we
    // expect to add those in the future. When we do, we'll prefix like this:
    // "tcf_purpose_consent_1", "tcf_purpose_legitimate_interest_2", etc.
    let type;
    let key;
    if (modelType === "customPurposesConsent") {
      type = "notice" as const;
      key = `${item.id}`;
    } else if (modelType === "purposesConsent") {
      type = "tcf_purpose_consent" as const;
      key = `${type}_${item.id}`;
    } else {
      type = "tcf_purpose_legitimate_interest" as const;
      key = `${type}_${item.id}`;
    }

    const preference: FidesEventDetailsPreference = {
      key,
      type,
    };

    const payload: UpdateEnabledIds = {
      newEnabledIds,
      modelType,
    };

    onChange(payload, eventTrigger, preference);
  };

  return (
    <div>
      <RadioGroup
        options={LEGAL_BASIS_OPTIONS}
        active={activeLegalBasisOption}
        onChange={setActiveLegalBasisOption}
      />
      <RecordsList<PurposeRecord | PrivacyNoticeWithBestTranslation>
        type="purposes"
        title={i18n.t("static.tcf.purposes")}
        items={
          activeData.customPurposes
            ? [...activeData.customPurposes, ...activeData.purposes]
            : activeData.purposes
        }
        enabledIds={
          activeData.enabledCustomPurposeIds
            ? [
                ...activeData.enabledCustomPurposeIds,
                ...activeData.enabledPurposeIds,
              ]
            : activeData.enabledPurposeIds
        }
        onToggle={(newEnabledIds, item, eventTrigger) => {
          const modelType =
            "bestTranslation" in item
              ? "customPurposesConsent"
              : activeData.purposeModelType;

          let filteredEnabledIds = newEnabledIds;
          if (modelType === "customPurposesConsent") {
            // filter out tcf purpose consent since we are just dealing with custom purposes
            filteredEnabledIds = newEnabledIds.filter(
              (id) => !activeData.enabledPurposeIds.includes(id),
            );
          } else if (activeData.enabledCustomPurposeIds) {
            /// filter out custom purpose consent since we are just dealing with TCF purposes
            filteredEnabledIds = newEnabledIds.filter(
              (id) => !activeData.enabledCustomPurposeIds?.includes(id),
            );
          }

          handleToggle(modelType, filteredEnabledIds, item, eventTrigger);
        }}
        renderToggleChild={(p, isCustomPurpose) => (
          <PurposeDetails
            type="purposes"
            purpose={p}
            isCustomPurpose={isCustomPurpose}
          />
        )}
        renderBadgeLabel={(item: RecordListItem) => {
          // Denote which purposes are standard IAB purposes if we have custom ones in the mix
          if (!activeData.customPurposes) {
            return undefined;
          }
          return item.bestTranslation ? "" : "IAB TCF";
        }}
        // This key forces a rerender when legal basis changes, which allows paging to reset properly
        key={`purpose-record-${activeLegalBasisOption.value}`}
      />
      <RecordsList<TCFSpecialPurposeRecord>
        type="specialPurposes"
        title={i18n.t("static.tcf.special_purposes")}
        items={activeData.specialPurposes}
        enabledIds={activeData.enabledSpecialPurposeIds}
        onToggle={(newEnabledIds, item, eventTrigger) =>
          handleToggle("specialPurposes", newEnabledIds, item, eventTrigger)
        }
        renderToggleChild={(p) => (
          <PurposeDetails type="specialPurposes" purpose={p} />
        )}
        hideToggles
        key={`special-purpose-record-${activeLegalBasisOption.value}`}
      />
    </div>
  );
};

export default TcfPurposes;
