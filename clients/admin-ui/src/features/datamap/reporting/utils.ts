import { ColumnsType } from "fidesui";

import { DATAMAP_GROUPING } from "~/types/api";

import { COLUMN_IDS } from "./constants";

/**
 * Extract the `key` from an Ant Design column definition, returning an empty
 * string when the key is absent.
 */
export const getColKey = (col: ColumnsType[number]): string =>
  String((col as { key?: string }).key ?? "");

export const getPrefixColumns = (groupBy: DATAMAP_GROUPING) => {
  let columnOrder: string[] = [];
  if (DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy) {
    columnOrder = [COLUMN_IDS.SYSTEM_NAME, COLUMN_IDS.DATA_USE];
  }
  if (DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy) {
    columnOrder = [COLUMN_IDS.DATA_USE, COLUMN_IDS.SYSTEM_NAME];
  }
  if (DATAMAP_GROUPING.SYSTEM_GROUP === groupBy) {
    columnOrder = [
      COLUMN_IDS.SYSTEM_GROUP,
      COLUMN_IDS.SYSTEM_GROUP_DATA_USES,
      COLUMN_IDS.SYSTEM_NAME,
      COLUMN_IDS.DATA_USE,
    ];
  }
  return columnOrder;
};

export const getColumnOrder = (
  groupBy: DATAMAP_GROUPING,
  columnIDs: string[],
) => {
  const prefixColumns = getPrefixColumns(groupBy);
  const prefixSet = new Set(prefixColumns);

  // Add any columns that aren't already in the prefix
  const remainingColumns = columnIDs.filter(
    (columnID) => !prefixSet.has(columnID),
  );

  return [...prefixColumns, ...remainingColumns];
};
