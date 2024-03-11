import { h } from "preact";

import { I18n } from "../../lib/i18n";

interface Option {
  label: string;
  value: string;
}

const RadioGroup = <T extends Option>({
  i18n,
  active,
  options,
  onChange,
}: {
  i18n: I18n;
  options: T[];
  active: T;
  onChange: (filter: T) => void;
}) => {
  const handleClick = (filter: T) => {
    onChange(filter);
  };

  return (
    <div className="fides-radio-button-group">
      {options.map((option) => {
        const selected = option.value === active.value;
        return (
          <button
            role="radio"
            type="button"
            aria-checked={selected}
            onClick={() => handleClick(option)}
            className="fides-radio-button"
          >
            {i18n.t(option.label)}
          </button>
        );
      })}
    </div>
  );
};

export default RadioGroup;
