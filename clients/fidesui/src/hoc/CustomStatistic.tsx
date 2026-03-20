import type { GlobalToken } from "antd";
import { Statistic, StatisticProps, theme } from "antd/lib";
import React from "react";

type AntColorTokenKey = Extract<keyof GlobalToken, `color${string}`>;

export type StatisticTrend = "up" | "down" | "neutral";

export type StatisticSize = "lg" | "sm";

export interface CustomStatisticProps extends StatisticProps {
  /**
   * Trend direction — controls the value colour.
   * - `up`: maps to `token.colorSuccess`
   * - `down`: maps to `token.colorError`
   * - `neutral`: maps to `token.colorText`
   * @default "neutral"
   */
  trend?: StatisticTrend;

  /**
   * Controls the font size of the statistic value.
   * - `lg`: maps to `token.fontSizeLG`
   * - `sm`: maps to `token.fontSizeSM`
   * - omitted: uses the default Ant Design Statistic font size
   */
  size?: StatisticSize;
}

/** Maps a trend direction to the corresponding Ant Design color-token key. */
const TREND_TOKEN_MAP: Record<StatisticTrend, AntColorTokenKey> = {
  up: "colorSuccess",
  down: "colorError",
  neutral: "colorText",
};

const SIZE_TOKEN_MAP: Record<StatisticSize, "fontSizeLG" | "fontSizeSM"> = {
  lg: "fontSizeLG",
  sm: "fontSizeSM",
};

const withCustomProps = (WrappedComponent: typeof Statistic) => {
  const WrappedStatistic = React.forwardRef<
    React.ComponentRef<typeof Statistic>,
    CustomStatisticProps
  >(({ trend = "neutral", size, valueStyle, ...props }, ref) => {
    const { token } = theme.useToken();
    const trendColor = token[TREND_TOKEN_MAP[trend]];
    const fontSize = size ? token[SIZE_TOKEN_MAP[size]] : undefined;
    return (
      <WrappedComponent
        ref={ref}
        valueStyle={{
          fontWeight: 600, // semibold
          color: trendColor,
          fontFamily: token.fontFamilyCode,
          ...(fontSize != null && { fontSize }),
          ...valueStyle, // allow per-instance overrides
        }}
        {...props}
      />
    );
  });

  WrappedStatistic.displayName = "CustomStatistic";
  return WrappedStatistic;
};

/**
 * Higher-order component that extends Ant Design's Statistic with trend-aware
 * colour and a semibold font-weight default.
 *
 * Additional props:
 * @param {"up" | "down" | "neutral"} [trend="neutral"] - Controls the colour of
 *   the statistic value. `"up"` uses the success colour, `"down"` the error colour,
 *   and `"neutral"` the default text colour.
 *
 * @example
 * <CustomStatistic title="Data Sharing" value="15,112,893" />
 *
 * @example
 * // Trend indicator below the main stat
 * <CustomStatistic
 *   trend="up"
 *   value="112,893"
 *   prefix={<ArrowUpOutlined />}
 *   valueStyle={{ fontSize: token.fontSize }}
 * />
 */
export const CustomStatistic = withCustomProps(Statistic);
