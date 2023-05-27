import { ColumnInstance } from "react-table";

import FilterMenu, {
  FieldValueToIsSelected,
} from "~/features/common/FilterMenu";
import { DatamapRow } from "~/features/datamap";

import { useMultifieldFilter } from "./helpers";

interface Props {
  column: ColumnInstance<DatamapRow> & {
    filterValue?: FieldValueToIsSelected | undefined;
    rows: DatamapRow[];
  };
}

const MultifieldFilter = ({ column }: Props) => {
  const { filterValue, clearFilterOptions, toggleFilterOption, options } =
    useMultifieldFilter(column);

  return (
    <FilterMenu
      filterValue={filterValue}
      onClearFilterOptions={clearFilterOptions}
      onToggleFilterOption={toggleFilterOption}
      options={options}
    />
  );
};

export default MultifieldFilter;
