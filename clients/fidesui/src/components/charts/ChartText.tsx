import { theme } from "antd";
import type { SVGProps } from "react";

import { CHART_TYPOGRAPHY } from "./chart-constants";

export interface ChartTextProps extends SVGProps<SVGTextElement> {
  x?: number;
  y?: number;
  fontFamily?: string;
  fill?: string;
  fillOpacity?: number;
}

export const ChartText = ({
  x,
  y,
  fontFamily,
  fill,
  fillOpacity,
  children,
  ...props
}: ChartTextProps) => {
  const { token } = theme.useToken();
  return (
    <text
      x={x}
      y={y}
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={token.fontSizeSM}
      fontFamily={fontFamily ?? token.fontFamilyCode}
      fontWeight={CHART_TYPOGRAPHY.fontWeight}
      letterSpacing={CHART_TYPOGRAPHY.letterSpacing}
      fill={fill}
      fillOpacity={fillOpacity}
      {...props}
    >
      {children}
    </text>
  );
};
