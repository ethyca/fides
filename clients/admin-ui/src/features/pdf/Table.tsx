import { StyleSheet, Text, View } from "@react-pdf/renderer";
import { palette } from "fidesui/src/palette/palette";

const styles = StyleSheet.create({
  table: {
    display: "flex",
    flexDirection: "column",
    width: "100%",
    fontSize: 12,
  },
  row: {
    display: "flex",
    flexDirection: "row",
    gap: 5,
    width: "100%",
    borderTopWidth: 0.5,
    borderTopColor: palette.FIDESUI_NEUTRAL_900,
    borderStyle: "solid",
    paddingVertical: 5,
    paddingHorizontal: 5,
  },
  tableHeader: {
    display: "flex",
    flexDirection: "row",
    gap: 5,
    width: "100%",
    backgroundColor: palette.FIDESUI_BG_SANDSTONE,
    borderTopWidth: 1.5,
    borderColor: palette.FIDESUI_NEUTRAL_900,
    borderBottomWidth: 1,
    borderStyle: "solid",
    paddingVertical: 5,
    paddingHorizontal: 5,
  },
  tableHeaderCell: {
    fontFamily: "BasierSquare",
    fontWeight: 500,
    fontSize: 10,
    textTransform: "uppercase",
  },
  cell: {
    fontFamily: "BasierSquare",
    color: palette.FIDESUI_NEUTRAL_700,
    fontWeight: 400,
    fontSize: 12,
  },
});

export const PdfTable = <
  T extends Record<string, React.ReactNode | string | undefined | null> &
    Record<"key", React.Key>,
>({
  data,
  columnDefs,
}: {
  data: Array<T>;
  columnDefs: Array<{ key: keyof T; title: string; flex: string }>;
}) => (
  <View style={styles.table}>
    <View style={styles.tableHeader}>
      {columnDefs.map(({ key, title, flex }) => (
        <Text style={[styles.tableHeaderCell, { flex }]} key={key.toString()}>
          {title}
        </Text>
      ))}
    </View>
    {data.map((row, i) => (
      <View
        break={false}
        wrap={false}
        style={[
          styles.row,
          { backgroundColor: i % 2 === 1 ? palette.FIDESUI_NEUTRAL_50 : "" },
        ]}
        key={row.key}
      >
        {columnDefs.map(({ key, flex }) => (
          <View
            break={false}
            style={[styles.cell, { flex }]}
            key={key.toString()}
          >
            {typeof row[key] === "string" ? (
              <Text break={false}>{row[key]}</Text>
            ) : (
              row[key]
            )}
          </View>
        ))}
      </View>
    ))}
  </View>
);
