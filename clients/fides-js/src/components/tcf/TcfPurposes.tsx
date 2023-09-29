import { h } from "preact";

import DataUseToggle from "../DataUseToggle";
import { PrivacyExperience } from "../../lib/consent-types";
import { TCFPurposeRecord } from "../../lib/tcf/types";
import { UpdateEnabledIds } from "./TcfOverlay";
import LegalBasisDropdown, {
  useLegalBasisDropdown,
} from "./LegalBasisDropdown";

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
  allPurposes,
  enabledIds,
  onChange,
  hideToggles,
}: {
  label: string;
  allPurposes: TCFPurposeRecord[] | undefined;
  enabledIds: string[];
  onChange: (newIds: string[]) => void;
  hideToggles?: boolean;
}) => {
  if (!allPurposes || allPurposes.length === 0) {
    return null;
  }

  const allChecked = allPurposes.every(
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
      onChange(allPurposes.map((p) => `${p.id}`));
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
      {allPurposes.map((p) => (
        <PurposeToggle
          purpose={p}
          onToggle={() => {
            handleToggle(p);
          }}
          checked={enabledIds.indexOf(`${p.id}`) !== -1}
          includeToggle={!hideToggles}
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
}) => {
  const { filtered, legalBasisFilter, setLegalBasisFilter } =
    useLegalBasisDropdown({
      allPurposes,
      allSpecialPurposes,
    });

  return (
    <div>
      <LegalBasisDropdown
        selected={legalBasisFilter}
        onSelect={(basis) => setLegalBasisFilter(basis)}
      />
      <PurposeBlock
        label="Purposes"
        allPurposes={filtered.purposes as TCFPurposeRecord[]}
        enabledIds={enabledPurposeIds}
        onChange={(newEnabledIds) =>
          onChange({ newEnabledIds, modelType: "purposes" })
        }
      />
      <PurposeBlock
        label="Special purposes"
        allPurposes={filtered.specialPurposes as TCFPurposeRecord[]}
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
