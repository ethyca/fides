import { theme } from "antd/lib";
import type { CSSProperties, ReactNode } from "react";
import { useMemo } from "react";

import type { RadarChartDataPoint } from "./RadarChart";

interface RadarTooltipContentProps {
  payload?: Array<{ payload: RadarChartDataPoint }>;
  tooltipContent?: (point: RadarChartDataPoint) => ReactNode;
}

export const RadarTooltipContent = ({
  payload: tooltipPayload,
  tooltipContent,
}: RadarTooltipContentProps) => {
  const { token } = theme.useToken();

  const style = useMemo<CSSProperties>(
    () => ({
      backgroundColor: token.colorBgElevated,
      borderRadius: token.borderRadius,
      padding: `${token.paddingXXS}px ${token.paddingXS}px`,
      boxShadow: token.boxShadow,
      fontSize: token.fontSizeSM,
    }),
    [token],
  );

  if (!tooltipPayload?.length) {
    return null;
  }
  const point = tooltipPayload[0].payload;
  return (
    <div style={style}>
      {tooltipContent
        ? tooltipContent(point)
        : `${point.subject}: ${point.value}`}
    </div>
  );
};
