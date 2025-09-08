import { DATAMAP_GROUPING } from "~/types/api";

import { COLUMN_IDS } from "./constants";

export const getGrouping = (groupBy?: DATAMAP_GROUPING) => {
  switch (groupBy) {
    case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
      return [COLUMN_IDS.DATA_USE];
    }
    case DATAMAP_GROUPING.SYSTEM_GROUP: {
      return [COLUMN_IDS.SYSTEM_GROUP];
    }
    default:
      return [COLUMN_IDS.SYSTEM_NAME];
  }
};

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
