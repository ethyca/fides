import { ResponsiveContainer } from "recharts";
import { Cell, Legend, Pie, PieChart, Tooltip } from "recharts";
import * as React from "react";

import { ChartContainer } from "../ChartContainer";
import { CustomTooltip } from "../CustomTooltip";
import { renderPieChartLabel } from "./PieChartLabel";
import type { FieldStatusData } from "../../types";

interface FieldStatusPieChartProps {
  data: FieldStatusData[];
  title?: string;
  height?: number;
}

/**
 * Pie chart component for displaying field status breakdown
 */
export const FieldStatusPieChart = ({
  data,
  title = "Field Status Breakdown",
  height = 300,
}: FieldStatusPieChartProps) => (
  <ChartContainer title={title} height={height}>
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={renderPieChartLabel}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  </ChartContainer>
);

