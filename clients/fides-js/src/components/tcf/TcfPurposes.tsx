import { h } from "preact";
import { useMemo, useState } from "preact/hooks";

import { UpdateEnabledIds } from "~/components/tcf/TcfTabs";

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
import EmbeddedVendorList from "./EmbeddedVendorList";
import RadioGroup from "./RadioGroup";
import RecordsList, { RecordListType } from "./RecordsList";

type TCFPurposeRecord =
  | TCFPurposeConsentRecord
  | TCFPurposeLegitimateInterestsRecord;

const PurposeDetails = ({
  i18n,
  type,
  purpose,
}: {
  i18n: I18n;
  type: RecordListType;
  purpose: TCFPurposeRecord;
}) => {
  const vendors = [...(purpose.vendors || []), ...(purpose.systems || [])];
  return (
    <div>
      <p className="fides-tcf-toggle-content">
        {i18n.t(`exp.tcf.${type}.${purpose.id}.description`)}
      </p>
      {purpose.illustrations.map((illustration, i) => (
        <p
          key={illustration}
          className="fides-tcf-illustration fides-background-dark"
        >
          {i18n.t(`exp.tcf.${type}.${purpose.id}.illustrations.${i}`)}
        </p>
      ))}

      <EmbeddedVendorList i18n={i18n} vendors={vendors} />
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
    [allPurposesConsent, allPurposesLegint],
  );

  const [activeLegalBasisOption, setActiveLegalBasisOption] = useState(
    LEGAL_BASIS_OPTIONS[0],
  );
  const activeData: {
    purposes: PurposeRecord[];
    purposeModelType: keyof EnabledIds;
    enabledPurposeIds: string[];
    specialPurposes: TCFSpecialPurposeRecord[];
    enabledSpecialPurposeIds: string[];
  } = useMemo(() => {
    const specialPurposes = allSpecialPurposes ?? [];
    if (activeLegalBasisOption.value === LegalBasisEnum.CONSENT.toString()) {
      return {
        purposes: uniquePurposes.filter((p) => p.isConsent),
        purposeModelType: "purposesConsent",
        enabledPurposeIds: enabledPurposeConsentIds,
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
        i18n={i18n}
        options={LEGAL_BASIS_OPTIONS}
        active={activeLegalBasisOption}
        onChange={setActiveLegalBasisOption}
      />
      <RecordsList<PurposeRecord>
        i18n={i18n}
        type="purposes"
        title={i18n.t("static.tcf.purposes")}
        items={activeData.purposes}
        enabledIds={activeData.enabledPurposeIds}
        onToggle={(newEnabledIds) =>
          onChange({ newEnabledIds, modelType: activeData.purposeModelType })
        }
        renderToggleChild={(p) => (
          <PurposeDetails i18n={i18n} type="purposes" purpose={p} />
        )}
        // This key forces a rerender when legal basis changes, which allows paging to reset properly
        key={`purpose-record-${activeLegalBasisOption.value}`}
      />
      <RecordsList<TCFSpecialPurposeRecord>
        i18n={i18n}
        type="specialPurposes"
        title={i18n.t("static.tcf.special_purposes")}
        items={activeData.specialPurposes}
        enabledIds={activeData.enabledSpecialPurposeIds}
        onToggle={(newEnabledIds) =>
          onChange({ newEnabledIds, modelType: "specialPurposes" })
        }
        renderToggleChild={(p) => (
          <PurposeDetails i18n={i18n} type="specialPurposes" purpose={p} />
        )}
        hideToggles
        key={`special-purpose-record-${activeLegalBasisOption.value}`}
      />
    </div>
  );
};

export default TcfPurposes;
