import type { ReactNode } from "react";

import type { RadarChartDataPoint } from "./RadarChart";
import styles from "./RadarTooltipContent.module.scss";

interface RadarTooltipContentProps {
  payload?: Array<{ payload: RadarChartDataPoint }>;
  tooltipContent?: (point: RadarChartDataPoint) => ReactNode;
}

export const RadarTooltipContent = ({
  payload: tooltipPayload,
  tooltipContent,
}: RadarTooltipContentProps) => {
  if (!tooltipPayload?.length) {
    return null;
  }
  const point = tooltipPayload[0].payload;
  if (tooltipContent) {
    return <>{tooltipContent(point)}</>;
  }
  return (
    <div className={styles.defaultTooltip}>
      {point.subject}: {point.value}
    </div>
  );
};
