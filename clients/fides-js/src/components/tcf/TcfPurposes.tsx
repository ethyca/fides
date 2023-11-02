import { h } from "preact";

import { useMemo, useState } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";
import {
  EnabledIds,
  LegalBasisEnum,
  PurposeRecord,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFSpecialPurposeRecord,
} from "../../lib/tcf/types";
import { UpdateEnabledIds } from "./TcfOverlay";
import { getUniquePurposeRecords } from "../../lib/tcf/purposes";
import RecordsList from "./RecordsList";
import { LEGAL_BASIS_OPTIONS } from "../../lib/tcf/constants";
import RadioGroup from "./RadioGroup";

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

  const [activeLegalBasisOption, setActiveLegalBasisOption] = useState(
    LEGAL_BASIS_OPTIONS[0]
  );
  const activeData: {
    purposes: PurposeRecord[];
    purposeModelType: keyof EnabledIds;
    enabledPurposeIds: string[];
    specialPurposes: TCFSpecialPurposeRecord[];
    enabledSpecialPurposeIds: string[];
  } = useMemo(() => {
    if (activeLegalBasisOption.value === LegalBasisEnum.CONSENT) {
      return {
        purposes: uniquePurposes.filter((p) => p.isConsent),
        purposeModelType: "purposesConsent",
        enabledPurposeIds: enabledPurposeConsentIds,
        // TODO: do we need to filter special purposes too?
        specialPurposes: allSpecialPurposes ?? [],
        enabledSpecialPurposeIds,
      };
    }
    return {
      purposes: uniquePurposes.filter((p) => p.isLegint),
      purposeModelType: "purposesLegint",
      enabledPurposeIds: enabledPurposeLegintIds,
      specialPurposes: allSpecialPurposes ?? [],
      enabledSpecialPurposeIds,
    };
  }, [
    activeLegalBasisOption,
    uniquePurposes,
    enabledPurposeConsentIds,
    enabledPurposeLegintIds,
    allSpecialPurposes,
    enabledSpecialPurposeIds,
  ]);

  return (
    <div>
      <RadioGroup
        options={LEGAL_BASIS_OPTIONS}
        active={activeLegalBasisOption}
        onChange={setActiveLegalBasisOption}
      />
      <RecordsList<PurposeRecord>
        title="Purposes"
        items={activeData.purposes}
        enabledIds={activeData.enabledPurposeIds}
        onToggle={(newEnabledIds) =>
          onChange({ newEnabledIds, modelType: activeData.purposeModelType })
        }
        renderToggleChild={(purpose) => <PurposeDetails purpose={purpose} />}
      />
      <RecordsList<TCFSpecialPurposeRecord>
        title="Special purposes"
        items={activeData.specialPurposes}
        enabledIds={activeData.enabledSpecialPurposeIds}
        onToggle={(newEnabledIds) =>
          onChange({ newEnabledIds, modelType: "specialPurposes" })
        }
        renderToggleChild={(p) => <PurposeDetails purpose={p} />}
        hideToggles
      />
    </div>
  );
};

export default TcfPurposes;
