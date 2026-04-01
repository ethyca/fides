import { theme } from "antd/lib";
import type { ComponentProps } from "react";
import { Text } from "recharts";

import { CHART_TYPOGRAPHY, LABEL_WIDTH } from "./chart-constants";

export type ChartTextProps = ComponentProps<typeof Text>;

export const ChartText = ({
  x,
  y,
  width = LABEL_WIDTH,
  fontFamily,
  fill,
  fillOpacity,
  children,
  maxLines = 1,
  ...props
}: ChartTextProps) => {
  const { token } = theme.useToken();
  return (
    <Text
      x={x}
      y={y}
      textAnchor="middle"
      verticalAnchor="middle"
      width={width}
      maxLines={maxLines}
      fontSize={token.fontSizeSM}
      fontFamily={fontFamily ?? token.fontFamilyCode}
      fontWeight={CHART_TYPOGRAPHY.fontWeight}
      letterSpacing={CHART_TYPOGRAPHY.letterSpacing}
      fill={fill}
      fillOpacity={fillOpacity}
      {...props}
    >
      {children}
    </Text>
  );
};
