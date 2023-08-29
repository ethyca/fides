import { h } from "preact";
import { LegalBasisForProcessingEnum } from "../../lib/tcf/types";

const LEGAL_BASES = [
  LegalBasisForProcessingEnum.CONSENT,
  LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS,
];

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
