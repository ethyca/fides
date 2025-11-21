import palette from "fidesui/src/palette/palette.module.scss";
import { ResponsiveContainer } from "recharts";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import * as React from "react";

import { ChartContainer } from "../ChartContainer";
import { CustomTooltip } from "../CustomTooltip";
import type { ClassificationActivityDataPoint } from "../../types";

interface ClassificationActivityChartProps {
  data: ClassificationActivityDataPoint[];
  title?: string;
  height?: number;
}

/**
 * Line chart component for displaying classification activity over time
 */
export const ClassificationActivityChart = ({
  data,
  title = "Classification Activity Over Time",
  height = 350,
}: ClassificationActivityChartProps) => (
  <ChartContainer title={title} height={height}>
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={palette.FIDESUI_NEUTRAL_200}
        />
        <XAxis
          dataKey="date"
          stroke={palette.FIDESUI_NEUTRAL_700}
          fontSize={12}
        />
        <YAxis stroke={palette.FIDESUI_NEUTRAL_700} fontSize={12} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          type="monotone"
          dataKey="discovered"
          stroke={palette.FIDESUI_INFO}
          strokeWidth={2}
          name="Discovered"
        />
        <Line
          type="monotone"
          dataKey="reviewed"
          stroke={palette.FIDESUI_WARNING}
          strokeWidth={2}
          name="Reviewed"
        />
        <Line
          type="monotone"
          dataKey="approved"
          stroke={palette.FIDESUI_SUCCESS}
          strokeWidth={2}
          name="Approved"
        />
      </LineChart>
    </ResponsiveContainer>
  </ChartContainer>
);
