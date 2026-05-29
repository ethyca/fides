import { Image, Page, StyleSheet, Text, View } from "@react-pdf/renderer";
import dayjs from "dayjs";
import { palette } from "fidesui/src/palette/palette";

// Create styles
const styles = StyleSheet.create({
  page: {
    paddingHorizontal: 40,
    paddingVertical: 40,
    flexDirection: "column",
    backgroundColor: palette.FIDESUI_BG_WHITE,
  },
  section: {
    fontFamily: "BasierSquare",
    fontSize: 12,
    paddingHorizontal: 10,
    flexGrow: 1,
    justifyContent: "space-evenly",
  },
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
  image: {
    height: 150,
    objectFit: "contain",
    objectPosition: "left center",
  },
  footerLabel: {
    fontFamily: "BasierSquare",
    textTransform: "uppercase",
    fontSize: 8,
    fontWeight: 600,
    color: palette.FIDESUI_NEUTRAL_600,
  },
  footerContent: {
    fontFamily: "BasierSquare",
    fontWeight: 400,
    fontSize: 10,
    letterSpacing: 0.75,
  },
});

// Create Document Component
export const TitlePage = ({
  monitorTitle,
  imageString,
  author,
  location,
}: {
  monitorTitle: string;
  imageString: string;
  author: string;
  location: string;
}) => (
  <Page size="A4" style={styles.page}>
    <View style={styles.section}>
      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
        <Text style={styles.title1}>Ethyca</Text>
        <View>
          <Text style={styles.title5}>Fides Website Monitor</Text>
          <Text style={styles.title5}>Continuous privacy observability</Text>
        </View>
      </View>
      <Text style={styles.title5}>{dayjs().format("YYYY·MM·DD")}</Text>
      <Text style={[styles.title4, { textTransform: "none" }]}>
        Website Audit
      </Text>

      {imageString && (
        /* This is not rendered to the dom and therefore doesn't need an alt */
        /* eslint-disable-next-line jsx-a11y/alt-text */
        <Image style={styles.image} src={{ uri: imageString }} />
      )}
      <View
        style={{
          display: "flex",
          width: "100%",
          marginTop: 300,
          paddingTop: 10,
          flexDirection: "row",
          justifySelf: "end",
          borderTopWidth: 1,
          borderColor: palette.FIDESUI_NEUTRAL_900,
        }}
      >
        <View
          style={{ display: "flex", flex: "33.33%", flexDirection: "column" }}
        >
          <Text style={styles.footerLabel}>Website</Text>
          <Text style={styles.footerContent}>{monitorTitle}</Text>
        </View>
        <View
          style={{ display: "flex", flex: "33.33%", flexDirection: "column" }}
        >
          <Text style={styles.footerLabel}>Location Scanned</Text>
          <Text style={styles.footerContent}>{location}</Text>
        </View>
        <View
          style={{ display: "flex", flex: "33.33%", flexDirection: "column" }}
        >
          <Text style={styles.footerLabel}>Author</Text>
          <Text style={styles.footerContent}>{author}</Text>
        </View>
      </View>
    </View>
  </Page>
);
