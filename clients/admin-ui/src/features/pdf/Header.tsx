import { StyleSheet, Text, View } from "@react-pdf/renderer";
import { palette } from "fidesui/src/palette/palette";

// Create styles
const styles = StyleSheet.create({
  title1: {
    fontFamily: "Eliza",
    fontSize: 50,
  },
  title2: {
    fontFamily: "BasierSquare",
    fontSize: 40,
  },
  title3: {
    fontSize: 20,
    fontFamily: "Eliza",
  },
  title4: {
    fontSize: 15,
    fontFamily: "BasierSquare",
    textTransform: "uppercase",
    fontWeight: 600,
  },
  title5: {
    fontSize: 10,
    fontFamily: "BasierSquare",
  },
  header: {
    borderBottomWidth: 1,
    borderBottomColor: palette.FIDESUI_NEUTRAL_900,
    borderStyle: "dotted",
    padding: 20,
    flexDirection: "row",
    justifyContent: "space-between",
  },
});

// Create Document Component
export const PdfHeader = ({
  section,
  title,
}: {
  title: string;
  section?: {
    title: string;
    index: number;
  };
}) => (
  <View style={styles.header} fixed>
    <Text style={[styles.title3, { fontSize: 12 }]}>{title}</Text>
    {section && (
      <Text
        style={styles.title5}
      >{`${section.index.toString().padStart(2, "0")} · ${section.title}`}</Text>
    )}
  </View>
);
