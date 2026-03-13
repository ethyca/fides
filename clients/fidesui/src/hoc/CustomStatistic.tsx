import type { GlobalToken } from "antd";
import { Statistic, StatisticProps, theme } from "antd/lib";
import React from "react";

import { FONT_FAMILY_DISPLAY } from "../ant-theme/default-theme";

type AntColorTokenKey = Extract<keyof GlobalToken, `color${string}`>;

export type StatisticTrend = "up" | "down" | "neutral";

export type StatisticValueVariant = "default" | "display";

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
   * Visual variant for the statistic value.
   * - `"default"`: standard semibold value at the Ant Design default size
   * - `"display"`: 2× larger (48 px) in the brand display font (Basier Square)
   * @default "default"
   */
  valueVariant?: StatisticValueVariant;
}

/** Maps a trend direction to the corresponding Ant Design color-token key. */
const TREND_TOKEN_MAP: Record<StatisticTrend, AntColorTokenKey> = {
  up: "colorSuccess",
  down: "colorError",
  neutral: "colorText",
};

const withCustomProps = (WrappedComponent: typeof Statistic) => {
  const WrappedStatistic = React.forwardRef<
    React.ComponentRef<typeof Statistic>,
    CustomStatisticProps
  >(
    (
      { trend = "neutral", valueVariant = "default", valueStyle, ...props },
      ref,
    ) => {
      const { token } = theme.useToken();
      const trendColor = token[TREND_TOKEN_MAP[trend]];

      const displayStyle: React.CSSProperties =
        valueVariant === "display"
          ? { fontSize: token.fontSizeHeading2, fontFamily: FONT_FAMILY_DISPLAY }
          : {};

      return (
        <WrappedComponent
          ref={ref}
          valueStyle={{
            fontWeight: 600, // semibold
            color: trendColor,
            ...displayStyle,
            ...valueStyle, // allow per-instance overrides
          }}
          {...props}
        />
      );
    },
  );

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
 * @param {"default" | "display"} [valueVariant="default"] - Controls the visual
 *   scale of the value. `"display"` renders at 48 px in the brand display font
 *   (Basier Square), intended for hero metrics on dashboards.
 *
 * @example
 * <CustomStatistic title="Data Sharing" value="15,112,893" />
 *
 * @example
 * // Hero metric with display variant
 * <CustomStatistic valueVariant="display" value={score} />
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
