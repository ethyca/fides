import { h } from "preact";

interface Option {
  label: string;
  value: string;
}

const RadioGroup = <T extends Option>({
  active,
  options,
  onChange,
}: {
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
            {option.label}
          </button>
        );
      })}
    </div>
  );
};

export default RadioGroup;
