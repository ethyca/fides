import { h } from "preact";
import DataUseToggle from "../DataUseToggle";
import { PrivacyExperience } from "../../lib/consent-types";
import { TCFPurposeRecord } from "~/lib/tcf/types";
import { EnabledIds, UpdateEnabledIds } from "./TcfOverlay";

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
  const handleToggleAllPurposes = () => {};
  const handleToggleAllSpecialPurposes = () => {};

  const handleTogglePurpose = (
    purpose: TCFPurposeRecord,
    modelType: keyof EnabledIds
  ) => {
    const purposeId = `${purpose.id}`;
    let enabled = enabledPurposeIds;
    if (modelType === "specialPurposes") {
      enabled = enabledSpecialPurposeIds;
    }
    // handle toggle off
    let updated = [];
    if (enabled.indexOf(purposeId) !== -1) {
      updated = enabled.filter((e) => e === purposeId);
    } else {
      updated = [...enabled, purposeId];
    }
    onChange({ newEnabledIds: updated, modelType });
  };

  return (
    <div>
      {allPurposes ? (
        <div>
          <DataUseToggle
            dataUse={{ key: "purposes", name: "Purposes" }}
            onToggle={handleToggleAllPurposes}
            checked={false}
          />
          {allPurposes.map((p) => (
            <PurposeToggle
              purpose={p}
              onToggle={() => {
                handleTogglePurpose(p, "purposes");
              }}
              checked={enabledPurposeIds.indexOf(`${p.id}`) !== -1}
            />
          ))}
        </div>
      ) : null}
      {allSpecialPurposes ? (
        <div>
          <DataUseToggle
            dataUse={{ key: "specialPurposes", name: "Special purposes" }}
            onToggle={handleToggleAllSpecialPurposes}
            checked={false}
          />
          {allSpecialPurposes.map((p) => (
            <PurposeToggle
              purpose={p}
              onToggle={() => {
                handleTogglePurpose(p, "specialPurposes");
              }}
              checked={enabledSpecialPurposeIds.indexOf(`${p.id}`) !== -1}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
};

export default TcfPurposes;
