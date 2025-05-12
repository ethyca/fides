import { theme } from "fidesui";
import _ from "lodash";

export const COLUMN_VERSION_DELIMITER = "::";

export const getTableTHandTDStyles = (noPadding?: boolean) =>
  noPadding
    ? { padding: "0px" }
    : {
        paddingLeft: theme.space[3],
        paddingRight: `calc(${theme.space[3]} - 5px)`, // 5px is the width of the resizer
        paddingTop: "0px",
        paddingBottom: "0px",
        borderRadius: "0px",
      };

export const columnExpandedVersion = (
  columnId: string,
  expandedColumns: string[],
) => {
  const expandedColumn = expandedColumns.find((c) => c.startsWith(columnId));
  return expandedColumn
    ? parseInt(expandedColumn.split(COLUMN_VERSION_DELIMITER)[1], 10)
    : undefined;
};

interface GetColumnHeaderTextProps {
  columnId: string | undefined;
  columnNameMap?: Record<string, string>;
}
/**
 * Get the header text for a column.
 * @param columnId The column ID.
 * @param columnNameMap A map of column IDs to display text.
 * @returns The header text.
 * @example
 * ```tsx
 * getColumnHeaderText({ columnId: "created_at", columnNameMap: { created_at: "Created at label" } });
 * // => "Created at label"
 * ```
 * @example
 * ```tsx
 * getColumnHeaderText({ columnId: "system_created_at" });
 * // => "Created at"
 * ```
 */
export const getColumnHeaderText = ({
  columnId,
  columnNameMap,
}: GetColumnHeaderTextProps): string => {
  if (!columnId) {
    return "";
  }
  const keyWithoutPrefix = columnId.replace(
    /^(system_|privacy_declaration_)/,
    "",
  );
  const nameFromId = _.upperFirst(keyWithoutPrefix.replaceAll("_", " "));
  return columnNameMap?.[columnId] || nameFromId;
};
