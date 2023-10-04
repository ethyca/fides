import { h } from "preact";

import DataUseToggle from "../DataUseToggle";
import { PrivacyExperience } from "../../lib/consent-types";
import {
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
} from "../../lib/tcf/types";
import { UpdateEnabledIds } from "./TcfOverlay";

type TCFPurposeRecord =
  | TCFPurposeConsentRecord
  | TCFPurposeLegitimateInterestsRecord;

const PurposeToggle = ({
  purpose,
  onToggle,
  checked,
  includeToggle = true,
}: {
  purpose: TCFPurposeRecord;
  onToggle: () => void;
  checked: boolean;
  includeToggle?: boolean;
}) => {
  const dataUse = { key: purpose.name, name: purpose.name };
  const vendors = [...(purpose.vendors || []), ...(purpose.systems || [])];
  return (
    <DataUseToggle
      dataUse={dataUse}
      checked={checked}
      onToggle={onToggle}
      includeToggle={includeToggle}
    >
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
    </DataUseToggle>
  );
};

const PurposeBlock = ({
  label,
  allPurposesConsent = [],
  enabledIdsConsent,
  onChange,
  hideToggles,
}: {
  label: string;
  allPurposesConsent: TCFPurposeConsentRecord[] | undefined;
  // TODO: support legint toggle (fides#4210)
  // allPurposesLegint: TCFPurposeLegitimateInterestsRecord[] | undefined;
  enabledIdsConsent: string[];
  onChange: (newIds: string[]) => void;
  hideToggles?: boolean;
}) => {
  const allChecked = allPurposesConsent.every(
    (p) => enabledIdsConsent.indexOf(`${p.id}`) !== -1
  );
  const handleToggle = (purpose: TCFPurposeRecord) => {
    const purposeId = `${purpose.id}`;
    if (enabledIdsConsent.indexOf(purposeId) !== -1) {
      onChange(enabledIdsConsent.filter((e) => e !== purposeId));
    } else {
      onChange([...enabledIdsConsent, purposeId]);
    }
  };
  const handleToggleAll = () => {
    if (allChecked) {
      onChange([]);
    } else {
      onChange(allPurposesConsent.map((p) => `${p.id}`));
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
      {allPurposesConsent.map((p) => (
        <PurposeToggle
          purpose={p}
          onToggle={() => {
            handleToggle(p);
          }}
          checked={enabledIdsConsent.indexOf(`${p.id}`) !== -1}
          includeToggle={!hideToggles}
        />
      ))}
    </div>
  );
};

const TcfPurposes = ({
  allPurposesConsent,
  allSpecialPurposes,
  enabledPurposeConsentIds,
  enabledSpecialPurposeIds,
  onChange,
}: {
  allPurposesConsent: TCFPurposeConsentRecord[] | undefined;
  enabledPurposeConsentIds: string[];
  allSpecialPurposes: PrivacyExperience["tcf_special_purposes"];
  // TODO: support legint toggle (fides#4210)
  // allPurposesLegint: TCFPurposeLegitimateInterestsRecord[] | undefined;
  // enabledPurposeLegintIds: string[];
  enabledSpecialPurposeIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => (
  <div>
    <PurposeBlock
      label="Purposes"
      allPurposesConsent={allPurposesConsent}
      enabledIdsConsent={enabledPurposeConsentIds}
      onChange={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "purposesConsent" })
      }
    />
    <PurposeBlock
      label="Special purposes"
      allPurposesConsent={allSpecialPurposes}
      enabledIdsConsent={enabledSpecialPurposeIds}
      onChange={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "specialPurposes" })
      }
      hideToggles
    />
  </div>
);

export default TcfPurposes;
