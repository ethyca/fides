import { Image, StyleSheet, Text, View } from "@react-pdf/renderer";
import { palette } from "fidesui/src/palette/palette";

import { VISUAL_COLORS } from "~/features/pdf/PdfStyles";
import { PdfTable } from "~/features/pdf/Table";
import { ClassificationBreakdownItem } from "~/types/api/models/ClassificationBreakdownItem";

import { getRootClassifications } from "../utils";

const styles = StyleSheet.create({
  chart: {
    height: 300,
    width: 300,
  },
});

export const MonitorReportDataElements = ({
  classificationsChart,
  classifications,
}: {
  classificationsChart: string;
  classifications: Array<ClassificationBreakdownItem>;
}) => (
  <View>
    {classificationsChart && (
      <View
        style={{
          flexDirection: "row",
          display: "flex",
          width: "100%",
          paddingHorizontal: 10,
          alignItems: "center",
        }}
      >
        {/* This is not rendered to the dom and therefore doesn't need an alt */}
        {/* eslint-disable-next-line jsx-a11y/alt-text */}
        <Image style={styles.chart} src={classificationsChart} />
        <View
          style={{
            display: "flex",
            flex: 1,
            flexDirection: "column",
            width: "100%",
          }}
        >
          {getRootClassifications(classifications)
            .slice(0, VISUAL_COLORS.length)
            .map(({ name, vendors }, i) => (
              <View
                style={{
                  display: "flex",
                  flexDirection: "row",
                  justifyContent: "space-between",
                }}
                key={name}
              >
                <View>
                  <View
                    style={{
                      height: 15,
                      width: 15,
                      backgroundColor: VISUAL_COLORS[i],
                    }}
                  />
                </View>
                <Text>{name}</Text>
                <Text>{vendors?.length}</Text>
              </View>
            ))}
        </View>
      </View>
    )}
    <PdfTable
      data={classifications.map(({ name, vendors, data_use }) => ({
        key: name,
        name: (
          <View
            style={{
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Text
              style={{
                color: palette.FIDESUI_NEUTRAL_900,
                fontWeight: 600,
              }}
            >
              {name}
            </Text>
            <Text
              style={{
                fontSize: 10,
              }}
            >
              {data_use}
            </Text>
          </View>
        ),
        vendors: vendors?.map((vendor) => vendor.name).join(", "),
      }))}
      columnDefs={[
        {
          key: "name",
          title: "Element",
          flex: "45%",
        },
        {
          key: "vendors",
          title: "Shared With",
          flex: "55%",
        },
      ]}
    />
  </View>
);
