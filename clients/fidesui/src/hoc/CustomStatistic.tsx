import { Statistic, StatisticProps, theme } from "antd/lib";
import React from "react";

export type StatisticTrend = "up" | "down" | "neutral";

export interface CustomStatisticProps extends StatisticProps {
  /**
   * Trend direction — controls the value colour.
   * - `up`: maps to `token.colorSuccess`
   * - `down`: maps to `token.colorError`
   * - `neutral`: maps to `token.colorText`
   * @default "neutral"
   */
  trend?: StatisticTrend;
}

const withCustomProps = (WrappedComponent: typeof Statistic) => {
  const WrappedStatistic = React.forwardRef<
    React.ComponentRef<typeof Statistic>,
    CustomStatisticProps
  >(({ trend = "neutral", valueStyle, ...props }, ref) => {
    const { token } = theme.useToken();

    /** Maps a trend direction to the corresponding Ant Design alias-token key. */
    const TREND_TOKEN_MAP: Record<StatisticTrend, keyof typeof token> = {
      up: "colorSuccess",
      down: "colorError",
      neutral: "colorText",
    };

    const trendColor = token[TREND_TOKEN_MAP[trend]];
    return (
      <WrappedComponent
        ref={ref}
        valueStyle={{
          fontWeight: 600, // semibold
          color: trendColor,
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
