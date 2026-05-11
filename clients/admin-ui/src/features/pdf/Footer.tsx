import { StyleSheet, Text, View } from "@react-pdf/renderer";
import { palette } from "fidesui/src/palette/palette";

const styles = StyleSheet.create({
  footer: {
    display: "flex",
    width: "100%",
    textAlign: "center",
    borderTopWidth: 1,
    borderTopColor: palette.FIDESUI_NEUTRAL_600,
    padding: 20,
    justifySelf: "end",
    fontSize: 10,
  },
});

// Create Document Component
export const PdfFooter = () => (
  <View style={styles.footer} fixed>
    <Text
      render={({ pageNumber }) => (pageNumber - 1).toString().padStart(2, "0")}
    />
  </View>
);
