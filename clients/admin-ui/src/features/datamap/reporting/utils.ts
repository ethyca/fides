import { DATAMAP_GROUPING } from "~/types/api";

import { COLUMN_IDS } from "./constants";

export const getGrouping = (groupBy?: DATAMAP_GROUPING) => {
  switch (groupBy) {
    case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
      return [COLUMN_IDS.DATA_USE];
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
  return columnOrder;
};

export const getColumnOrder = (
  groupBy: DATAMAP_GROUPING,
  columnIDs: string[],
) => {
  let columnOrder: string[] = getPrefixColumns(groupBy);
  columnOrder = columnOrder.concat(
    columnIDs.filter(
      (columnID) =>
        columnID !== COLUMN_IDS.SYSTEM_NAME && columnID !== COLUMN_IDS.DATA_USE,
    ),
  );
  return columnOrder;
};
