import { h } from "preact";

import { useI18n } from "../../lib/i18n/i18n-context";

interface Option {
  /**
   * i18n Message ID to use for i18n.t(...), e.g. i18n.t("static.tcf.consent")
   */
  i18nMessageID: string;
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
  const { i18n } = useI18n();
  const handleClick = (filter: T) => {
    onChange(filter);
  };

  return (
    <div className="fides-radio-button-group">
      {options.map((option) => {
        const selected = option.value === active.value;
        return (
          <button
            key={option.value}
            role="radio"
            type="button"
            aria-checked={selected}
            onClick={() => handleClick(option)}
            className="fides-radio-button"
          >
            {i18n.t(option.i18nMessageID)}
          </button>
        );
      })}
    </div>
  );
};

export default RadioGroup;
