import { h } from "preact";
import { useState } from "preact/hooks";

const FilterButtons = () => {
  const filters = [{ name: "All vendors" }, { name: "Global vendors" }];
  const [activeButtonIndex, setActiveButtonIndex] = useState(0);

  return (
    <div className="fides-filter-button-group">
      {filters.map(({ name }, idx) => {
        const selected = idx === activeButtonIndex;
        return (
          <button
            role="radio"
            type="button"
            aria-checked={selected}
            onClick={() => setActiveButtonIndex(idx)}
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
