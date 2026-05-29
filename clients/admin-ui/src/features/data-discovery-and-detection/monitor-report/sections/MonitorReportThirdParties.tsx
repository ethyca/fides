import { Image, StyleSheet, Text, View } from "@react-pdf/renderer";
import { palette } from "fidesui/src/palette/palette";

import { pluralize } from "~/features/common/utils";
import { VISUAL_COLORS } from "~/features/pdf/PdfStyles";
import { PdfTable } from "~/features/pdf/Table";
import { VendorBreakdownItem } from "~/types/api/models/VendorBreakdownItem";

const styles = StyleSheet.create({
  chart: {
    height: 300,
    width: 300,
  },
});

export const MonitorReportsThirdParties = ({
  vendorsChart,
  vendors,
}: {
  vendorsChart: string;
  vendors: Array<VendorBreakdownItem>;
}) => (
  <>
    <Text>
      {`All ${vendors.length} vendor systems identified by Fides, categorized against our internal vendor taxonomy. Data shared columns pair a human-readable label from Fides. Data use is what drives the policy enforcement in the platform`}
    </Text>
    {vendorsChart && (
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
        <Image style={styles.chart} src={vendorsChart} />
        <View
          style={{
            display: "flex",
            flex: 1,
            flexDirection: "column",
            width: "100%",
          }}
        >
          {vendors
            .slice(0, VISUAL_COLORS.length)
            .map(({ name, resource_count }, i) => (
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
                <Text>{resource_count}</Text>
              </View>
            ))}
        </View>
      </View>
    )}
    <PdfTable
      data={vendors.map(({ name, locations, resource_count, data_uses }) => ({
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
              {`${resource_count ?? 0} ${pluralize(resource_count ?? 0, "resource", "resources")}`}
            </Text>
          </View>
        ),
        locations: locations?.map((location) => location.toLocaleUpperCase()),
        dataShared: data_uses?.map((dataUse) => dataUse.name).join(", "),
      }))}
      columnDefs={[
        {
          key: "name",
          title: "Third Party",
          flex: "35%",
        },
        {
          key: "dataShared",
          title: "Data Shared",
          flex: "50%",
        },
        {
          key: "locations",
          title: "Locations",
          flex: "15%",
        },
      ]}
    />
  </>
);
