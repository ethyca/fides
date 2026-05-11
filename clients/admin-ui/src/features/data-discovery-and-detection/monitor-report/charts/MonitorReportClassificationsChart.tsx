import { Pie, PieChart } from "recharts";

import { VISUAL_COLORS } from "~/features/pdf/PdfStyles";
import { ClassificationBreakdownItem } from "~/types/api/models/ClassificationBreakdownItem";

const MonitorReportClassificationsChart = ({
  classifications,
}: {
  classifications: Array<ClassificationBreakdownItem>;
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
      data={classifications?.map(({ vendors, name }, i) => ({
        vendorsCount: vendors?.length,
        name,
        fill: VISUAL_COLORS[i],
      }))}
      dataKey="vendorsCount"
      nameKey="name"
      isAnimationActive={false}
      innerRadius="30%"
    />
  </PieChart>
);

export default MonitorReportClassificationsChart;
