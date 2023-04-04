import React, { useContext } from 'react';
import { ColumnInstance, Row } from 'react-table';

import { DatamapRow } from '~/features/datamap';
import DatamapTableContext from '~/features/datamap/datamap-table/DatamapTableContext';
import type { FieldValueToIsSelected } from '~/features/datamap/datamap-table/filters/accordion-multifield-filter/AccordionMultifieldFilter';

export const accordionMultifieldFilter = <D extends Record<string, unknown>>(
  rows: Row<D>[],
  columnIds: string[],
  filterValue: FieldValueToIsSelected
) => {
  // The useFilters hook passes a single column id.
  const columnId = columnIds[0];
  return rows.filter((row) => {
    const fieldValue = row.values[columnId];
    return filterValue[fieldValue];
  });
};

export const useAccordionMultifieldFilter = <D extends Record<string, unknown>>(
  props: Omit<ColumnInstance<D>, 'filterValue'> & {
    filterValue?: FieldValueToIsSelected;
    rows: DatamapRow[];
  }
) => {
  const { tableInstance } = useContext(DatamapTableContext);

  const options = React.useMemo(() => {
    const columnValues = new Set<string>();
    props.preFilteredRows.forEach((row) => {
      columnValues.add(row.values[props.id]);
    });
    return Array.from(columnValues);
  }, [props.id, props.preFilteredRows]);

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
    props.setFilter(clearedFilters);
  };

  const toggleFilterOption = (
    option: keyof FieldValueToIsSelected,
    isSelected: boolean
  ) => {
    const updatedFilter = {
      ...(props.filterValue ?? initialFilterValue),
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
      tableInstance?.setAllFilters(
        tableInstance?.state.filters.filter((f) => f.id !== props.id)
      );
    } else {
      props.setFilter(updatedFilter);
    }
  };

  return {
    filterValue: props.filterValue ?? initialFilterValue,
    clearFilterOptions,
    toggleFilterOption,
    options,
    header: props.Header,
  };
};
