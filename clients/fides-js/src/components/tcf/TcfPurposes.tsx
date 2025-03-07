import { h } from "preact";
import { useMemo, useState } from "preact/hooks";

import { UpdateEnabledIds } from "~/components/tcf/TcfTabs";

import { ConsentMechanism, PrivacyExperience } from "../../lib/consent-types";
import { FidesEventDetailsTrigger } from "../../lib/events";
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
        onToggle={(newEnabledIds, item, eventTrigger) =>
          onChange(
            {
              newEnabledIds,
              // @ts-ignore
              modelType: item.bestTranslation
                ? "customPurposesConsent"
                : activeData.purposeModelType,
            },
            eventTrigger,
          )
        }
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
        onToggle={(newEnabledIds, _, eventTrigger) =>
          onChange(
            { newEnabledIds, modelType: "specialPurposes" },
            eventTrigger,
          )
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
