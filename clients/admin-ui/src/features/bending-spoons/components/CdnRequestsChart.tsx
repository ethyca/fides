import palette from "fidesui/src/palette/palette.module.scss";
import { forwardRef } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { CHART_DATA } from "../constants";

const SANS =
  "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

const CdnRequestsChart = forwardRef<HTMLDivElement>((_, ref) => (
  <div
    ref={ref}
    style={{
      width: 912,
      backgroundColor: "transparent",
      padding: "32px 36px 28px",
    }}
  >
    <div style={{ height: 360 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={CHART_DATA}
          margin={{ top: 10, right: 0, bottom: 4, left: -8 }}
          barCategoryGap="20%"
        >
          <defs>
            <linearGradient id="bar-olive" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#8a8c76" stopOpacity={1} />
              <stop offset="100%" stopColor="#a5a690" stopOpacity={1} />
            </linearGradient>
          </defs>
          <CartesianGrid
            stroke={palette.FIDESUI_NEUTRAL_400}
            strokeDasharray="4 4"
            vertical={false}
          />
          <XAxis
            dataKey="month"
            axisLine={false}
            tickLine={false}
            tick={{
              fontSize: 12,
              fill: palette.FIDESUI_NEUTRAL_800,
              fontFamily: SANS,
            }}
            dy={10}
          />
          <YAxis
            type="number"
            domain={[0, 1000]}
            ticks={[0, 200, 400, 600, 800, 1000]}
            axisLine={false}
            tickLine={false}
            tick={{
              fontSize: 11,
              fill: palette.FIDESUI_NEUTRAL_700,
              fontFamily: SANS,
            }}
            tickFormatter={(v: number) => (v === 1000 ? "1B" : `${v}M`)}
          />
          <Tooltip
            formatter={(v: number) => [`${v}M`, "CDN Requests"]}
            contentStyle={{
              borderRadius: 8,
              border: "none",
              fontSize: 12,
              fontFamily: SANS,
              boxShadow:
                "0 4px 16px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.06)",
              padding: "8px 14px",
            }}
            cursor={{ fill: "rgba(43,46,53,0.04)" }}
          />
          <Bar
            dataKey="cdn"
            fill="url(#bar-olive)"
            radius={[2, 2, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </div>
));

CdnRequestsChart.displayName = "CdnRequestsChart";
export default CdnRequestsChart;
