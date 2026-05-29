import { Page, StyleSheet, Text, View } from "@react-pdf/renderer";
import { palette } from "fidesui/src/palette/palette";

import { PdfFooter } from "~/features/pdf/Footer";
import { PdfHeader } from "~/features/pdf/Header";
import { HeaderStyles } from "~/features/pdf/PdfStyles";
import { TableOfContentsPdf } from "~/features/pdf/TableOfContents";
import { TitlePage } from "~/features/pdf/TitlePage";
import { PdfWrapper } from "~/features/pdf/Wrapper";
import { AggregateStatisticsResponse } from "~/types/api";
import { ClassificationBreakdownItem } from "~/types/api/models/ClassificationBreakdownItem";
import { VendorBreakdownItem } from "~/types/api/models/VendorBreakdownItem";

import { MonitorReportDataElements } from "./sections/MonitorReportDataElements";
import { MonitorReportSummary } from "./sections/MonitorReportSummary";
import { MonitorReportsThirdParties } from "./sections/MonitorReportThirdParties";

const styles = StyleSheet.create({
  page: {
    paddingHorizontal: 40,
    paddingTop: 40,
    flexDirection: "column",
    backgroundColor: palette.FIDESUI_BG_WHITE,
    justifyContent: "space-evenly",
  },
  section: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
    fontFamily: "BasierSquare",
    fontSize: 12,
    marginVertical: 10,
    paddingVertical: 10,
    flexGrow: 1,
  },
});

const SECTIONS = [
  {
    title: "Summary",
    description:
      "Dashboard of detected systems, scripts, cookies, and consent issues.",
  },
  {
    title: "Third Parties",
    description: "All vendors observed, categorized with data they receive.",
  },
  {
    title: "Data Elements",
    description:
      "Fides data-use taxonomy labels and the vendors receiving each.",
  },
] as const;

export const MonitorReport = ({
  author,
  classifications,
  classificationsChart,
  imageSrc,
  location,
  monitorTitle,
  stats,
  vendors,
  vendorsChart,
}: {
  author: string;
  classifications: Array<ClassificationBreakdownItem>;
  classificationsChart: string;
  imageSrc: string;
  location: string;
  monitorTitle: string;
  stats: AggregateStatisticsResponse;
  vendors: Array<VendorBreakdownItem>;
  vendorsChart: string;
}) => (
  <PdfWrapper>
    <TitlePage
      imageString={imageSrc}
      monitorTitle={monitorTitle}
      location={location}
      author={author}
    />
    <Page size="A4" style={styles.page}>
      <PdfHeader title="Ethyca" />
      <View style={styles.section}>
        <Text style={HeaderStyles.h4}>Contents</Text>
        <Text style={HeaderStyles.h1}>Report details</Text>
        <Text style={[HeaderStyles.h4, { fontSize: 12 }]}>
          Table of contents
        </Text>
        <TableOfContentsPdf sections={SECTIONS} />
      </View>
      <PdfFooter />
    </Page>
    {SECTIONS.map(({ title }, sectionIndex) => (
      <Page size="A4" style={styles.page} key={title}>
        <PdfHeader
          section={{ title, index: sectionIndex + 1 }}
          title="Ethyca"
        />
        <View style={styles.section}>
          <Text style={HeaderStyles.h5}>{`Chapter ${sectionIndex + 1}`}</Text>
          <Text style={HeaderStyles.h1}>{title}</Text>
          {title === "Summary" && (
            <MonitorReportSummary
              classifications={classifications}
              vendors={vendors}
              stats={stats}
              monitorTitle={monitorTitle}
            />
          )}
          {title === "Data Elements" && (
            <MonitorReportDataElements
              classifications={classifications}
              classificationsChart={classificationsChart}
            />
          )}
          {title === "Third Parties" && (
            <MonitorReportsThirdParties
              vendors={vendors}
              vendorsChart={vendorsChart}
            />
          )}
        </View>
        <PdfFooter />
      </Page>
    ))}
  </PdfWrapper>
);
