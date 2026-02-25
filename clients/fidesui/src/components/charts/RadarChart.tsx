import { theme } from "antd";
import { useId } from "react";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
} from "recharts";

/** Maps to Ant Design's colorSuccess / colorWarning / colorError tokens. */
export type RadarPointStatus = "success" | "warning" | "error";

export interface RadarChartDataPoint {
  subject: string;
  value: number;
  /**
   * When provided, the dot and label for this point are colored using the
   * corresponding Ant Design token (colorSuccess / colorWarning / colorError).
   * Points without a status render with the default chart color.
   */
  status?: RadarPointStatus;
}

const EMPTY_PLACEHOLDER_DATA: RadarChartDataPoint[] = [
  { subject: "", value: 10 },
  { subject: "", value: 10 },
  { subject: "", value: 10 },
  { subject: "", value: 10 },
  { subject: "", value: 10 },
  { subject: "", value: 10 },
];

export interface RadarChartProps {
  data?: RadarChartDataPoint[] | null;
  color?: string;
  animationDuration?: number;
}

const RadarChart = ({
  data,
  color,
  animationDuration = 1500,
}: RadarChartProps) => {
  const { token } = theme.useToken();
  const empty = !data?.length;
  const chartColor = color ?? token.colorText;

  const uid = useId().replace(/:/g, "");
  const gradientId = `radar-gradient-${uid}`;

  const STATUS_COLORS: Record<RadarPointStatus, string> = {
    success: token.colorSuccess,
    warning: token.colorWarning,
    error: token.colorError,
  };

  return (
    <div className="h-full w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart
          data={empty ? EMPTY_PLACEHOLDER_DATA : data}
          cx="50%"
          cy="50%"
          outerRadius="70%"
        >
          <defs>
            <radialGradient id={gradientId} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={chartColor} stopOpacity={0.02} />
              <stop offset="100%" stopColor={chartColor} stopOpacity={0.2} />
            </radialGradient>
          </defs>

          <PolarGrid
            stroke={chartColor}
            strokeWidth={0.5}
            strokeOpacity={0.15}
          />

          {/* Lock radial scale to 0-100 */}
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />

          {!empty && (
            <PolarAngleAxis
              dataKey="subject"
              tick={(props: Record<string, unknown>) => {
                const { x, y, payload } = props as {
                  x: number;
                  y: number;
                  payload: { value: string; index: number };
                };
                const point = data![payload.index];
                const statusColor = point?.status
                  ? STATUS_COLORS[point.status]
                  : undefined;

                return (
                  <text
                    x={x}
                    y={y}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize={11}
                    fontWeight={statusColor ? 600 : 400}
                    fill={statusColor ?? chartColor}
                    fillOpacity={statusColor ? 1 : 0.45}
                  >
                    {payload.value}
                  </text>
                );
              }}
            />
          )}

          <Radar
            dataKey="value"
            stroke={chartColor}
            strokeWidth={1.5}
            strokeOpacity={0.8}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill={`url(#${gradientId})`}
            dot={(props: Record<string, unknown>) => {
              const {
                cx: dotCx,
                cy: dotCy,
                index,
              } = props as {
                cx: number;
                cy: number;
                index: number;
              };
              const point = empty ? undefined : data![index];
              if (!point?.status) return <g key={`dot-${index}`} />;

              return (
                <circle
                  key={`dot-${index}`}
                  cx={dotCx}
                  cy={dotCy}
                  r={3.5}
                  fill={STATUS_COLORS[point.status]}
                  stroke="none"
                />
              );
            }}
            activeDot={false}
            isAnimationActive={!empty}
            animationDuration={animationDuration}
            animationEasing="ease-in-out"
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RadarChart;
