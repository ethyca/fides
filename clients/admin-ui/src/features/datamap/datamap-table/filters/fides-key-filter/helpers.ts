import React from 'react';
import { ColumnInstance, Row } from 'react-table';

/**
 * This filter is specifically for System Fides keys. These keys are kept in
 * sync with the SpatialDatamap through the filters slice.
 * For example, given a table like:
 * | #  | System Fides Key |
 * | -- | --               |
 * | 1  | demo_system      |
 * | 2  | demo_system      |
 * | 3  | fides_system  |
 * | 4  | fides_system  |
 * The user could filter by:
 *   - Clicking "demo_system" in the map = Rows 1 & 2
 *   - Selecting only "fidesctl_system" in the menu = Rows 3 & 4.
 */
export const fidesKeyFilter = <D extends Record<string, unknown>>(
  rows: Row<D>[],
  columnIds: string[],
  filterValue: Set<string> = new Set()
) => {
  // The useFilters hook passes a single column id.
  const columnId = columnIds[0];

  return rows.filter((row) => {
    const fidesKey: string = row.values[columnId];
    return filterValue.has(fidesKey);
  });
};

export const useFidesKeyFilter = <D extends Record<string, unknown>>({
  id,
  filterValue,
  preFilteredRows,
}: Omit<ColumnInstance<D>, 'filterValue' | 'setFilter'> & {
  filterValue?: Set<string>;
}) => {
  const allFidesKeys = React.useMemo(() => {
    const rowValueSet = new Set<string>();
    preFilteredRows.forEach((row) => {
      rowValueSet.add(row.values[id]);
    });
    return Array.from(rowValueSet);
  }, [id, preFilteredRows]);

  const toggle = React.useCallback(
    (fidesKey: string, isSelected: boolean) => {
      const newSet = new Set(filterValue ?? allFidesKeys);
      if (isSelected) {
        newSet.add(fidesKey);
      } else {
        newSet.delete(fidesKey);
      }
    },
    [filterValue, allFidesKeys]
  );

  const clear = React.useCallback(() => ({}), []);

  return {
    options: allFidesKeys,
    selectedSet: filterValue ?? new Set(allFidesKeys),
    toggle,
    clear,
  };
};
