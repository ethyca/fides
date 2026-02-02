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
import type { ConsentRateDataPoint } from "../../types";

interface ConsentRatesChartProps {
  data: ConsentRateDataPoint[];
  title?: string;
  height?: number;
}

/**
 * Line chart component for displaying opt in vs opt out rates over time
 */
export const ConsentRatesChart = ({
  data,
  title = "Opt In vs Opt Out Rates Over Time",
  height = 350,
}: ConsentRatesChartProps) => (
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
          dataKey="optIn"
          stroke={palette.FIDESUI_SUCCESS}
          strokeWidth={2}
          name="Opt In"
        />
        <Line
          type="monotone"
          dataKey="optOut"
          stroke={palette.FIDESUI_ERROR}
          strokeWidth={2}
          name="Opt Out"
        />
      </LineChart>
    </ResponsiveContainer>
  </ChartContainer>
);

