import { Pie, PieChart } from "recharts";

import { VISUAL_COLORS } from "~/features/pdf/PdfStyles";
import { VendorBreakdownItem } from "~/types/api/models/VendorBreakdownItem";

const MonitorReportVendorsChart = ({
  vendors,
}: {
  vendors: Array<VendorBreakdownItem>;
}) => (
  <PieChart
    barCategoryGap="10%"
    barGap={4}
    height={1200}
    width={1200}
    responsive
    style={{ aspectRatio: 1 }}
    endAngle={360}
    startAngle={0}
  >
    <Pie
      data={vendors?.map(({ resource_count, name }, i) => ({
        resource_count,
        name,
        fill: VISUAL_COLORS[i],
      }))}
      dataKey="resource_count"
      nameKey="name"
      isAnimationActive={false}
      innerRadius="30%"
    />
  </PieChart>
);

export default MonitorReportVendorsChart;
