import { h } from "preact";

import { useMemo } from "preact/hooks";
import DataUseToggle from "../DataUseToggle";
import { PrivacyExperience } from "../../lib/consent-types";
import {
  PurposeRecord,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
} from "../../lib/tcf/types";
import { UpdateEnabledIds } from "./TcfOverlay";
import RecordsByLegalBasis from "./RecordsByLegalBasis";
import { getUniquePurposeRecords } from "../../lib/tcf/purposes";

type TCFPurposeRecord =
  | TCFPurposeConsentRecord
  | TCFPurposeLegitimateInterestsRecord;

const PurposeDetails = ({ purpose }: { purpose: TCFPurposeRecord }) => {
  const vendors = [...(purpose.vendors || []), ...(purpose.systems || [])];
  return (
    <div>
      <p className="fides-tcf-toggle-content">{purpose.description}</p>
      {purpose.illustrations.map((illustration) => (
        <p className="fides-tcf-illustration fides-background-dark">
          {illustration}
        </p>
      ))}

      {vendors.length ? (
        <p className="fides-tcf-toggle-content fides-background-dark fides-tcf-purpose-vendor">
          <span className="fides-tcf-purpose-vendor-title">
            Vendors we use for this purpose
            <span>{vendors.length} vendor(s)</span>
          </span>
          <ul className="fides-tcf-purpose-vendor-list">
            {vendors.map((v) => (
              <li>{v.name}</li>
            ))}
          </ul>
        </p>
      ) : null}
    </div>
  );
};

const SpecialPurposeBlock = ({
  label,
  allSpecialPurposes = [],
  enabledIds,
  onChange,
  hideToggles,
}: {
  label: string;
  allSpecialPurposes: TCFPurposeConsentRecord[] | undefined;
  enabledIds: string[];
  onChange: (newIds: string[]) => void;
  hideToggles?: boolean;
}) => {
  const allChecked = allSpecialPurposes.every(
    (p) => enabledIds.indexOf(`${p.id}`) !== -1
  );
  const handleToggle = (purpose: TCFPurposeRecord) => {
    const purposeId = `${purpose.id}`;
    if (enabledIds.indexOf(purposeId) !== -1) {
      onChange(enabledIds.filter((e) => e !== purposeId));
    } else {
      onChange([...enabledIds, purposeId]);
    }
  };
  const handleToggleAll = () => {
    if (allChecked) {
      onChange([]);
    } else {
      onChange(allSpecialPurposes.map((p) => `${p.id}`));
    }
  };

  return (
    <div>
      <DataUseToggle
        dataUse={{ key: label, name: label }}
        onToggle={handleToggleAll}
        checked={allChecked}
        isHeader
        includeToggle={!hideToggles}
      />
      {allSpecialPurposes.map((p) => {
        const dataUse = { key: p.name, name: p.name };
        return (
          <DataUseToggle
            dataUse={dataUse}
            checked={enabledIds.indexOf(`${p.id}`) !== -1}
            onToggle={() => {
              handleToggle(p);
            }}
            includeToggle={!hideToggles}
          >
            <PurposeDetails purpose={p} />
          </DataUseToggle>
        );
      })}
    </div>
  );
};

const TcfPurposes = ({
  allPurposesConsent = [],
  allPurposesLegint = [],
  allSpecialPurposes,
  enabledPurposeConsentIds,
  enabledPurposeLegintIds,
  enabledSpecialPurposeIds,
  onChange,
}: {
  allPurposesConsent: TCFPurposeConsentRecord[] | undefined;
  enabledPurposeConsentIds: string[];
  allSpecialPurposes: PrivacyExperience["tcf_special_purposes"];
  allPurposesLegint: TCFPurposeLegitimateInterestsRecord[] | undefined;
  enabledPurposeLegintIds: string[];
  enabledSpecialPurposeIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => {
  const { uniquePurposes } = useMemo(
    () =>
      getUniquePurposeRecords({
        consentPurposes: allPurposesConsent,
        legintPurposes: allPurposesLegint,
      }),
    [allPurposesConsent, allPurposesLegint]
  );

  return (
    <div>
      <RecordsByLegalBasis<PurposeRecord>
        title="Purposes"
        items={uniquePurposes}
        enabledConsentIds={enabledPurposeConsentIds}
        enabledLegintIds={enabledPurposeLegintIds}
        onToggle={onChange}
        renderToggleChild={(purpose) => <PurposeDetails purpose={purpose} />}
        consentModelType="purposesConsent"
        legintModelType="purposesLegint"
      />
      <SpecialPurposeBlock
        label="Special purposes"
        allSpecialPurposes={allSpecialPurposes}
        enabledIds={enabledSpecialPurposeIds}
        onChange={(newEnabledIds) =>
          onChange({ newEnabledIds, modelType: "specialPurposes" })
        }
        hideToggles
      />
    </div>
  );
};

export default TcfPurposes;
