import { StyleSheet, Text, View } from "@react-pdf/renderer";
import { palette } from "fidesui/src/palette/palette";

import { HeaderStyles, TextStyles } from "./PdfStyles";

const styles = StyleSheet.create({
  layout: {
    flexDirection: "row",
    gap: 40,
    alignContent: "center",
    borderBottomWidth: 1,
    borderBottomColor: palette.FIDESUI_NEUTRAL_400,
    padding: 10,
  },
  tableOfContentsItem: {
    flexDirection: "column",
  },
});

export const TableOfContentsPdf = ({
  sections,
}: {
  sections: ReadonlyArray<{ title: string; description: string }>;
}) => (
  <>
    {sections.map(({ title, description }, i) => (
      <View style={styles.layout} key={title}>
        <Text style={[TextStyles.medium, TextStyles.highlight]}>
          {(i + 1).toString().padStart(2, "0")}
        </Text>
        <View style={styles.tableOfContentsItem}>
          <Text style={[HeaderStyles.h3]}>{title}</Text>
          <Text style={[TextStyles.medium, TextStyles.secondary]}>
            {description}
          </Text>
        </View>
      </View>
    ))}
  </>
);
