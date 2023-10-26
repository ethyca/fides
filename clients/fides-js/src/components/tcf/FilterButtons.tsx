import { h } from "preact";
import { useState } from "preact/hooks";

interface Filter {
  name: string;
}

const FilterButtons = ({
  filters,
  onChange,
}: {
  filters: Filter[];
  onChange: (idx: number) => void;
}) => {
  const [activeButtonIndex, setActiveButtonIndex] = useState(0);
  const handleClick = (idx: number) => {
    setActiveButtonIndex(idx);
    onChange(idx);
  };

  return (
    <div className="fides-filter-button-group">
      {filters.map(({ name }, idx) => {
        const selected = idx === activeButtonIndex;
        return (
          <button
            role="radio"
            type="button"
            aria-checked={selected}
            onClick={() => handleClick(idx)}
            className="fides-filter-button"
          >
            {name}
          </button>
        );
      })}
    </div>
  );
};

export default FilterButtons;
