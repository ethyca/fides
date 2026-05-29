import { StyleSheet, Text, View } from "@react-pdf/renderer";
import { palette } from "fidesui/src/palette/palette";

import { HeaderStyles } from "~/features/pdf/PdfStyles";
import { AggregateStatisticsResponse } from "~/types/api";
import { ClassificationBreakdownItem } from "~/types/api/models/ClassificationBreakdownItem";
import { VendorBreakdownItem } from "~/types/api/models/VendorBreakdownItem";

const styles = StyleSheet.create({
  statBox: {
    display: "flex",
    flex: "50% 50% 50%",
    borderColor: palette.FIDESUI_NEUTRAL_600,
    borderWidth: 0.5,
    padding: 20,
  },
});

export const MonitorReportSummary = ({
  monitorTitle,
  vendors,
  classifications,
  stats,
}: {
  monitorTitle: string;
  vendors: Array<VendorBreakdownItem>;
  classifications: Array<ClassificationBreakdownItem>;
  stats: AggregateStatisticsResponse;
}) => (
  <View style={{ display: "flex", gap: 20, flexDirection: "column" }}>
    <Text>{`Fides Monitor continuously observed ${monitorTitle} accross  99 pages and 3 consent states.`}</Text>
    <View
      style={{
        display: "flex",
        flexDirection: "row",
        flexWrap: "wrap",
      }}
    >
      <View style={styles.statBox}>
        <Text>Third-parties</Text>
        <Text style={HeaderStyles.h1}>{vendors.length}</Text>
        <Text>Identified vendors across distinct domains</Text>
      </View>

      <View style={styles.statBox}>
        <Text>Scripts</Text>
        <Text style={HeaderStyles.h1}>
          {(stats.resource_type_counts?.javascript_tag ?? 0) +
            (stats.resource_type_counts?.browser_request ?? 0)}
        </Text>
        <Text>JS tags · browser requests</Text>
      </View>

      <View style={styles.statBox}>
        <Text>Data Elements</Text>
        <Text style={HeaderStyles.h1}>{classifications.length}</Text>
        <Text>Fides taxonomy data uses in scope</Text>
      </View>

      <View style={styles.statBox}>
        <Text>Cookies</Text>
        <Text style={HeaderStyles.h1}>
          {stats.resource_type_counts?.cookie}
        </Text>
        <Text>First and third party</Text>
      </View>
    </View>
  </View>
);
