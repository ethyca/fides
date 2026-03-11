import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";
import classNames from "classnames";
import { Card, Col, Row, Skeleton, Statistic } from "fidesui";
import { Sparkline } from "fidesui";

import { nFormatter } from "~/features/common/utils";
import type { TrendMetric } from "~/features/dashboard/dashboard.slice";

import cardStyles from "./dashboard-card.module.scss";

const TREND_CARD_TITLES = [
  "Data sharing",
  "Active users",
  "Total requests",
  "Consent rate",
];

const PERCENTAGE_INDICES = new Set([0, 1, 3]);

const formatTrendValue = (metric: TrendMetric, index: number): string => {
  if (PERCENTAGE_INDICES.has(index)) {
    return `${Math.round(metric.value * 100)}%`;
  }
  return nFormatter(metric.value);
};

const formatTrendDiff = (metric: TrendMetric, index: number): string => {
  const abs = Math.abs(metric.diff);
  if (PERCENTAGE_INDICES.has(index)) {
    return `${Math.round(abs * 100)}%`;
  }
  return nFormatter(abs);
};

interface TrendCardsProps {
  metrics: TrendMetric[];
}

const TrendCards = ({ metrics }: TrendCardsProps) => (
  <Row gutter={24}>
    {TREND_CARD_TITLES.map((title, i) => {
      const metric = metrics[i];
      return (
        <Col key={title} xs={24} sm={12} md={6}>
          <Card
            size="small"
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
                  value={formatTrendValue(metric, i)}
                />
                {metric.diff !== 0 && (
                  <Statistic
                    trend={metric.diff > 0 ? "up" : "down"}
                    value={formatTrendDiff(metric, i)}
                    prefix={
                      metric.diff > 0 ? (
                        <ArrowUpOutlined />
                      ) : (
                        <ArrowDownOutlined />
                      )
                    }
                    className={cardStyles.smallStatistic}
                  />
                )}
              </>
            ) : (
              <Skeleton active paragraph={false} />
            )}
          </Card>
        </Col>
      );
    })}
  </Row>
);

export default TrendCards;
