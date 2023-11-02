import { h } from "preact";
import { useState } from "preact/hooks";

interface Filter {
  label: string;
  value: string;
}

const FilterButtons = <T extends Filter>({
  filters,
  onChange,
}: {
  filters: T[];
  onChange: (filter: T) => void;
}) => {
  const [active, setActive] = useState(filters[0]);
  const handleClick = (filter: T) => {
    setActive(filter);
    onChange(filter);
  };

  return (
    <div className="fides-filter-button-group">
      {filters.map((filter) => {
        const selected = filter.value === active.value;
        return (
          <button
            role="radio"
            type="button"
            aria-checked={selected}
            onClick={() => handleClick(filter)}
            className="fides-filter-button"
          >
            {filter.label}
          </button>
        );
      })}
    </div>
  );
};

export default FilterButtons;
