import { h } from "preact";

import { useMemo, useState } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";
import { I18n } from "../../lib/i18n";
import { LEGAL_BASIS_OPTIONS } from "../../lib/tcf/constants";
import { getUniquePurposeRecords, hasLegalBasis } from "../../lib/tcf/purposes";
import {
  EnabledIds,
  LegalBasisEnum,
  PurposeRecord,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFSpecialPurposeRecord,
} from "../../lib/tcf/types";
import { UpdateEnabledIds } from "./TcfOverlay";
import RecordsList from "./RecordsList";
import RadioGroup from "./RadioGroup";
import EmbeddedVendorList from "./EmbeddedVendorList";

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

      <EmbeddedVendorList vendors={vendors} />
    </div>
  );
};

const TcfPurposes = ({
  i18n,
  allPurposesConsent = [],
  allPurposesLegint = [],
  allSpecialPurposes,
  enabledPurposeConsentIds,
  enabledPurposeLegintIds,
  enabledSpecialPurposeIds,
  onChange,
}: {
  i18n: I18n;
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
    const specialPurposes = allSpecialPurposes ?? [];
    if (activeLegalBasisOption.value === LegalBasisEnum.CONSENT) {
      return {
        purposes: uniquePurposes.filter((p) => p.isConsent),
        purposeModelType: "purposesConsent",
        enabledPurposeIds: enabledPurposeConsentIds,
        specialPurposes: specialPurposes.filter((sp) =>
          hasLegalBasis(sp, LegalBasisEnum.CONSENT)
        ),
        enabledSpecialPurposeIds,
      };
    }
    return {
      purposes: uniquePurposes.filter((p) => p.isLegint),
      purposeModelType: "purposesLegint",
      enabledPurposeIds: enabledPurposeLegintIds,
      specialPurposes: specialPurposes.filter((sp) =>
        hasLegalBasis(sp, LegalBasisEnum.LEGITIMATE_INTERESTS)
      ),
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

  // static.tcf.purposes
  // static.tcf.special_purposes
  return (
    <div>
      <RadioGroup
        options={LEGAL_BASIS_OPTIONS}
        active={activeLegalBasisOption}
        onChange={setActiveLegalBasisOption}
      />
      <RecordsList<PurposeRecord>
        i18n={i18n}
        title="Purposes"
        items={activeData.purposes}
        enabledIds={activeData.enabledPurposeIds}
        onToggle={(newEnabledIds) =>
          onChange({ newEnabledIds, modelType: activeData.purposeModelType })
        }
        renderToggleChild={(purpose) => <PurposeDetails purpose={purpose} />}
        // This key forces a rerender when legal basis changes, which allows paging to reset properly
        key={`purpose-record-${activeLegalBasisOption.value}`}
      />
      <RecordsList<TCFSpecialPurposeRecord>
        i18n={i18n}
        title="Special purposes"
        items={activeData.specialPurposes}
        enabledIds={activeData.enabledSpecialPurposeIds}
        onToggle={(newEnabledIds) =>
          onChange({ newEnabledIds, modelType: "specialPurposes" })
        }
        renderToggleChild={(p) => <PurposeDetails purpose={p} />}
        hideToggles
        key={`special-purpose-record-${activeLegalBasisOption.value}`}
      />
    </div>
  );
};

export default TcfPurposes;
