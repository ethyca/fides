import { theme } from "fidesui";

export const COLUMN_VERSION_DELIMITER = "::";

export const getTableTHandTDStyles = (cellId: string) =>
  cellId === "select"
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
