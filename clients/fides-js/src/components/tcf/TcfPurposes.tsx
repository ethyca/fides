import { h } from "preact";

import DataUseToggle from "../DataUseToggle";
import { PrivacyExperience } from "../../lib/consent-types";
import { TCFPurposeRecord } from "../../lib/tcf/types";
import { UpdateEnabledIds } from "./TcfOverlay";

const PurposeToggle = ({
  purpose,
  onToggle,
  checked,
}: {
  purpose: TCFPurposeRecord;
  onToggle: () => void;
  checked: boolean;
}) => {
  const dataUse = { key: purpose.name, name: purpose.name };
  return (
    <DataUseToggle dataUse={dataUse} checked={checked} onToggle={onToggle}>
      <div>
        <p className="fides-tcf-toggle-content">{purpose.description}</p>
        <p className="fides-tcf-illustration fides-background-dark">
          {purpose.illustrations[0]}
        </p>
        {purpose.vendors && purpose.vendors.length ? (
          <p className="fides-tcf-toggle-content fides-background-dark fides-tcf-purpose-vendor">
            <span className="fides-tcf-purpose-vendor-title">
              Vendors we use for this purpose
            </span>
            <ul className="fides-tcf-purpose-vendor-list">
              {purpose.vendors.map((v) => (
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
  allPurposes,
  enabledIds,
  onChange,
}: {
  label: string;
  allPurposes: TCFPurposeRecord[] | undefined;
  enabledIds: string[];
  onChange: (newIds: string[]) => void;
}) => {
  if (!allPurposes || allPurposes.length === 0) {
    return null;
  }

  const allChecked = allPurposes.length === enabledIds.length;
  const handleToggle = (purpose: TCFPurposeRecord) => {
    const purposeId = `${purpose.id}`;
    if (enabledIds.indexOf(purposeId) !== -1) {
      onChange(enabledIds.filter((e) => e === purposeId));
    } else {
      onChange([...enabledIds, purposeId]);
    }
  };
  const handleToggleAll = () => {
    if (allChecked) {
      onChange([]);
    } else {
      onChange(allPurposes.map((p) => `${p.id}`));
    }
  };

  return (
    <div>
      <DataUseToggle
        dataUse={{ key: label, name: label }}
        onToggle={handleToggleAll}
        checked={allChecked}
      />
      {allPurposes.map((p) => (
        <PurposeToggle
          purpose={p}
          onToggle={() => {
            handleToggle(p);
          }}
          checked={enabledIds.indexOf(`${p.id}`) !== -1}
        />
      ))}
    </div>
  );
};

const TcfPurposes = ({
  allPurposes,
  allSpecialPurposes,
  enabledPurposeIds,
  enabledSpecialPurposeIds,
  onChange,
}: {
  allPurposes: PrivacyExperience["tcf_purposes"];
  allSpecialPurposes: PrivacyExperience["tcf_special_purposes"];
  enabledPurposeIds: string[];
  enabledSpecialPurposeIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => (
  <div>
    <PurposeBlock
      label="Purposes"
      allPurposes={allPurposes}
      enabledIds={enabledPurposeIds}
      onChange={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "purposes" })
      }
    />
    <PurposeBlock
      label="Special purposes"
      allPurposes={allSpecialPurposes}
      enabledIds={enabledSpecialPurposeIds}
      onChange={(newEnabledIds) =>
        onChange({ newEnabledIds, modelType: "specialPurposes" })
      }
    />
  </div>
);

export default TcfPurposes;
