import { DATAMAP_GROUPING, DatamapReport } from "~/types/api";

import { COLUMN_IDS } from "./constants";

export type DatamapReportRow = DatamapReport & {
  rowKey: string;
  /** Number of rows this group spans (set on the first row of each group). */
  groupRowSpan?: number;
  /** Whether this row is not the first in its group (grouping cell should be hidden). */
  groupRowHidden?: boolean;
  // Custom field columns have dynamic keys
  [key: string]: unknown;
};

type DatamapReportInput = DatamapReport & Record<string, unknown>;

/**
 * Returns the field key used for grouping based on the active grouping mode.
 */
export const getGroupKey = (groupBy: DATAMAP_GROUPING): keyof DatamapReport => {
  switch (groupBy) {
    case DATAMAP_GROUPING.DATA_USE_SYSTEM:
      return COLUMN_IDS.DATA_USE as keyof DatamapReport;
    case DATAMAP_GROUPING.SYSTEM_GROUP:
      return COLUMN_IDS.SYSTEM_GROUP as keyof DatamapReport;
    default:
      return COLUMN_IDS.SYSTEM_NAME as keyof DatamapReport;
  }
};

/**
 * Prepares flat datamap report rows with rowSpan metadata for Ant Design Table
 * cell merging.
 *
 * Rows are ordered by group. The first row of each group gets `groupRowSpan`
 * set to the group size; subsequent rows get `groupRowHidden: true`. The
 * grouping column uses these values in `onCell` to set `rowSpan` / `rowSpan: 0`.
 */
export const groupDatamapRows = (
  items: DatamapReportInput[],
  groupBy: DATAMAP_GROUPING,
): DatamapReportRow[] => {
  if (!items.length) {
    return [];
  }

  const groupKey = getGroupKey(groupBy);

  // Collect groups in insertion order
  const groups = new Map<string, DatamapReportInput[]>();
  items.forEach((item) => {
    const keyValue = String(
      (item as Record<string, unknown>)[groupKey] ?? "unknown",
    );
    const existing = groups.get(keyValue);
    if (existing) {
      existing.push(item);
    } else {
      groups.set(keyValue, [item]);
    }
  });

  // Flatten groups back into rows with span metadata
  const result: DatamapReportRow[] = [];
  groups.forEach((groupItems, key) => {
    groupItems.forEach((item, idx) => {
      const itemKey = item.fides_key
        ? `${key}-${item.fides_key}-${item.declaration_name ?? "none"}-${idx}`
        : `${key}-${idx}`;
      result.push({
        ...item,
        rowKey: itemKey,
        ...(idx === 0
          ? { groupRowSpan: groupItems.length }
          : { groupRowHidden: true }),
      });
    });
  });

  return result;
};
