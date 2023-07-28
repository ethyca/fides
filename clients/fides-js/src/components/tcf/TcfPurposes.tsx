import { h } from "preact";
import DataUseToggle from "../DataUseToggle";
import { PrivacyExperience } from "../../lib/consent-types";
import { TCFPurposeRecord } from "~/lib/tcf/types";

const PurposeToggle = ({
  purpose,
  onToggle,
}: {
  purpose: TCFPurposeRecord;
  onToggle: () => void;
}) => {
  const dataUse = { key: purpose.name, name: purpose.name };
  return (
    <DataUseToggle dataUse={dataUse} checked={false} onToggle={onToggle}>
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
  purposes,
  specialPurposes,
}: {
  purposes: PrivacyExperience["tcf_purposes"];
  specialPurposes: PrivacyExperience["tcf_special_purposes"];
}) => {
  const handleToggleAllPurposes = () => {};
  const handleToggleAllSpecialPurposes = () => {};

  const handleTogglePurpose = (purpose: TCFPurposeRecord) => {
    console.log({ purpose });
  };

  return (
    <div>
      {purposes ? (
        <div>
          <DataUseToggle
            dataUse={{ key: "purposes", name: "Purposes" }}
            onToggle={handleToggleAllPurposes}
            checked={false}
          />
          {purposes.map((p) => (
            <PurposeToggle
              purpose={p}
              onToggle={() => {
                handleTogglePurpose(p);
              }}
            />
          ))}
        </div>
      ) : null}
      {specialPurposes ? (
        <div>
          <DataUseToggle
            dataUse={{ key: "specialPurposes", name: "Special purposes" }}
            onToggle={handleToggleAllSpecialPurposes}
            checked={false}
          />
          {specialPurposes.map((p) => (
            <PurposeToggle
              purpose={p}
              onToggle={() => {
                handleTogglePurpose(p);
              }}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
};

export default TcfPurposes;
