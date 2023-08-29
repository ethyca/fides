import { h } from "preact";
import { useMemo, useState } from "preact/hooks";
import {
  LegalBasisForProcessingEnum,
  TCFPurposeRecord,
} from "../../lib/tcf/types";

const LEGAL_BASES = [
  LegalBasisForProcessingEnum.CONSENT,
  LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS,
];

export const useLegalBasisDropdown = ({
  allPurposes,
  allSpecialPurposes,
}: {
  allPurposes: Pick<TCFPurposeRecord, "legal_bases">[] | undefined;
  allSpecialPurposes: Pick<TCFPurposeRecord, "legal_bases">[] | undefined;
}) => {
  const [legalBasisFilter, setLegalBasisFilter] = useState(
    LegalBasisForProcessingEnum.CONSENT
  );
  const filtered = useMemo(() => {
    const purposes = allPurposes
      ? allPurposes.filter(
          (p) => p.legal_bases?.indexOf(legalBasisFilter) !== -1
        )
      : [];
    const specialPurposes = allSpecialPurposes
      ? allSpecialPurposes.filter(
          (sp) => sp.legal_bases?.indexOf(legalBasisFilter) !== -1
        )
      : [];
    return { purposes, specialPurposes };
  }, [allPurposes, allSpecialPurposes, legalBasisFilter]);

  return { filtered, legalBasisFilter, setLegalBasisFilter };
};

const LegalBasisDropdown = ({
  selected,
  onSelect,
}: {
  selected: LegalBasisForProcessingEnum;
  onSelect: (option: LegalBasisForProcessingEnum) => void;
}) => {
  const id = `legal-basis-select`;
  const handleChange = (evt: h.JSX.TargetedEvent<HTMLSelectElement, Event>) => {
    const target = evt.target as HTMLSelectElement;
    if (target) {
      onSelect(target.value as LegalBasisForProcessingEnum);
    }
  };
  return (
    <label htmlFor={id}>
      Filter purposes by legal basis
      <select
        name="legal-basis"
        id={id}
        value={selected}
        onChange={handleChange}
        className="fides-select-dropdown"
      >
        {LEGAL_BASES.map((basis) => (
          <option key={basis} value={basis}>
            {basis}
          </option>
        ))}
      </select>
    </label>
  );
};

export default LegalBasisDropdown;
