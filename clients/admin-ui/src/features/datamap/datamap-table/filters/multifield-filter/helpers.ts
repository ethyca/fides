import React from 'react';
import { ColumnInstance, Row } from 'react-table';

import type { FieldValueToIsSelected } from '~/features/common/FilterMenu';

import { DatamapRow } from '../../../datamap.slice';

/**
 * The this filter function allows every value in a column to be (de)selected.
 * For example, given a table like:
 *  | Num | Alpha |
 *  |--   |--     |
 *  | 1   | A     |
 *  | 1   | B     |
 *  | 2   | A     |
 *  | 2   | B     |
 * The user could filter by:
 *   - Num = "1" or "2"
 *   - Alpha = "A" or "B"
 *   - Or any combination.
 */
export const multifieldFilter = <D extends Record<string, unknown>>(
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

export const useMultifieldFilter = <D extends Record<string, unknown>>({
  id,
  filterValue,
  preFilteredRows,
  setFilter,
}: Omit<ColumnInstance<D>, 'filterValue'> & {
  filterValue?: FieldValueToIsSelected;
  rows: DatamapRow[];
}) => {
  const options = React.useMemo(() => {
    const columnValues = new Set<string>();
    preFilteredRows.forEach((row) => {
      columnValues.add(row.values[id]);
    });
    return Array.from(columnValues);
  }, [id, preFilteredRows]);

  const initialFilterValue = React.useMemo(() => {
    const optionToSelected: FieldValueToIsSelected = {};
    options.forEach((option) => {
      optionToSelected[option] = true;
    });
    return optionToSelected;
  }, [options]);

  const clearFilterOptions = () => {
    options.forEach((option) => {
      setFilter({
        [option]: false,
      });
    });
  };

  const toggleFilterOption = (
    option: keyof FieldValueToIsSelected,
    isSelected: boolean
  ) => {
    setFilter({
      ...(filterValue ?? initialFilterValue),
      [option]: isSelected,
    });
  };

  return {
    filterValue: filterValue ?? initialFilterValue,
    clearFilterOptions,
    toggleFilterOption,
    options,
  };
};
