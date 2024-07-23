import { Column, Row } from "@tanstack/react-table";
import React, { useContext } from "react";

import { DatamapRow } from "~/features/datamap";
import DatamapTableContext from "~/features/datamap/datamap-table/DatamapTableContext";
import type { FieldValueToIsSelected } from "~/features/datamap/datamap-table/filters/accordion-multifield-filter/AccordionMultifieldFilter";

export const accordionMultifieldFilter = <T extends Record<string, any>>(
  row: Row<T>,
  columnId: string,
  filterValue: FieldValueToIsSelected,
) => {
  const fieldValue = row.original[columnId];
  return filterValue[fieldValue];
};
interface AccordionMultifieldFilterProps {
  column: Column<DatamapRow>;
}
export const useAccordionMultifieldFilter = ({
  column,
}: AccordionMultifieldFilterProps) => {
  const { tableInstance } = useContext(DatamapTableContext);

  const options = React.useMemo(() => {
    const columnValues = Array.from(column.getFacetedUniqueValues().keys());
    return columnValues;
  }, [column]);

  const initialFilterValue = React.useMemo(() => {
    const optionToSelected: FieldValueToIsSelected = {};
    options.forEach((option) => {
      optionToSelected[option] = false;
    });
    return optionToSelected;
  }, [options]);

  const clearFilterOptions = () => {
    const clearedFilters: { [key: string]: boolean } = {};
    options.forEach((option) => {
      clearedFilters[option] = false;
    });
    column.setFilterValue(clearedFilters);
  };

  const toggleFilterOption = (
    option: keyof FieldValueToIsSelected,
    isSelected: boolean,
  ) => {
    const updatedFilter = {
      ...(column.getFilterValue() ?? initialFilterValue),
      [option]: isSelected,
    };

    if (Object.values(updatedFilter).every((f) => !f)) {
      /*
       * This is only way to remove a filter object from `react-table`.
       * It's required because the accordion filter sets all options
       * to false by default. If all options are false then
       * it filters out all the data. We only want to add the filter
       * object when at least one option is toggled to true.
       */
      tableInstance?.setColumnFilters(
        tableInstance
          ?.getState()
          .columnFilters.filter((f) => f.id !== column.id),
      );
    } else {
      column.setFilterValue(updatedFilter);
    }
  };

  return {
    filterValue:
      (column.getFilterValue() as FieldValueToIsSelected) ??
      (initialFilterValue as FieldValueToIsSelected),
    clearFilterOptions,
    toggleFilterOption,
    options,
    header: column.columnDef.header,
  };
};
