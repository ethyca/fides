import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons"; // eslint-disable-line import/no-extraneous-dependencies
import classNames from "classnames";
import { Card, Skeleton, Sparkline, Statistic } from "fidesui";

import { nFormatter } from "~/features/common/utils";
import type { TrendMetric } from "~/features/dashboard/dashboard.slice";

import cardStyles from "./dashboard-card.module.scss";

type TrendFormat = "number" | "percentage";

interface TrendCardProps {
  title: string;
  metric: TrendMetric | undefined;
  format?: TrendFormat;
}

const formatValue = (value: number, format: TrendFormat) => {
  if (format === "percentage") {
    return Math.round(value * 100);
  }
  return nFormatter(value);
};

const formatDiff = (diff: number, format: TrendFormat) => {
  const abs = Math.abs(diff);
  if (format === "percentage") {
    return Math.round(abs * 100);
  }
  return nFormatter(abs);
};

const TrendCard = ({ title, metric, format = "number" }: TrendCardProps) => {
  const suffix = format === "percentage" ? "%" : undefined;

  return (
    <Card
      variant="borderless"
      title={title}
      className={classNames("overflow-clip h-full", cardStyles.dashboardCard)}
      showTitleDivider={false}
      cover={
        metric?.history ? (
          <div className="h-16">
            <Sparkline data={metric.history} />
          </div>
        ) : undefined
      }
      coverPosition="bottom"
    >
      {metric ? (
        <>
          <Statistic
            valueVariant="display"
            value={formatValue(metric.value, format)}
            suffix={suffix}
          />
          {metric.diff !== 0 && (
            <Statistic
              trend={metric.diff > 0 ? "up" : "down"}
              value={formatDiff(metric.diff, format)}
              suffix={suffix}
              prefix={
                metric.diff > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />
              }
              className={cardStyles.smallStatistic}
            />
          )}
        </>
      ) : (
        <Skeleton active paragraph={false} />
      )}
    </Card>
  );
};

export default TrendCard;
