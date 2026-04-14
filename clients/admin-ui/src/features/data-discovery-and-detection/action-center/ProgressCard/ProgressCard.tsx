import classNames from "classnames";
import {
  Badge,
  Descriptions,
  EnterExitList,
  Flex,
  Paragraph,
  StackedBarChart,
  StackedBarChartProps,
  Statistic,
  Text,
  Title,
  Tooltip,
} from "fidesui";
import { PropsWithChildren } from "react";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";
import { nFormatter } from "~/features/common/utils";

type NumericStat = {
  label: string;
  count: number;
};

type PercentStat = {
  label: string;
  value: number;
};

export interface ProgressCardProps {
  title: string;
  subtitle: string;
  progress: {
    label: string;
    percent?: number;
    numerator?: number;
    denominator?: number;
  };
  barChartProps?: StackedBarChartProps;
  numericStats?: {
    data: NumericStat[];
    label: string;
  };
  percentageStats?: {
    data: PercentStat[];
    label: string;
  };
  lastUpdated?: string;
  compact?: boolean;
  disabled?: boolean;
}

export const ProgressCard = ({
  title,
  subtitle,
  barChartProps,
  percentageStats,
  numericStats,
  lastUpdated,
  disabled,
  compact,
}: PropsWithChildren<ProgressCardProps>) => {
  const relativeTime = useRelativeTime(
    lastUpdated ? new Date(lastUpdated) : new Date(),
  );

  return (
    <Flex
      rootClassName={classNames(
        "transition duration-1000 w-full",
        disabled ? "opacity-50" : "opacity-100",
      )}
      vertical
    >
      {!compact && (
        <Flex justify="space-between" align="baseline">
          <Title level={5} className="whitespace-nowrap">
            {title}
          </Title>
          <Paragraph
            type="secondary"
            className="!my-0 w-full self-end text-right text-xs"
            ellipsis={{
              rows: 1,
              tooltip: { title: relativeTime },
            }}
          >
            {relativeTime}
          </Paragraph>
        </Flex>
      )}
      <EnterExitList
        dataSource={[
          (barChartProps?.data?.progress?.classified ?? 0) +
            (barChartProps?.data?.progress?.unlabeled ?? 0),
        ]}
        itemKey={(key) => key}
        renderItem={(item) => (
          <Tooltip
            color="white"
            rootClassName="max-w-[400px]"
            title={
              numericStats && (
                <div>
                  <Text type="secondary" strong className="text-xs">
                    {numericStats.label}
                  </Text>
                  {numericStats.data.length > 0 ? (
                    <Descriptions size="small" column={1} layout="horizontal">
                      {numericStats.data?.map(({ label, count }) => (
                        <Descriptions.Item label={label} key={label}>
                          {nFormatter(count)}
                        </Descriptions.Item>
                      ))}
                    </Descriptions>
                  ) : (
                    <div className="text-xs">None</div>
                  )}
                </div>
              )
            }
          >
            <Statistic value={nFormatter(item)} />
          </Tooltip>
        )}
      />
      <Text>resources need review{!compact && <> across {subtitle}</>}</Text>
      <div>
        {barChartProps && <StackedBarChart {...barChartProps} hideTooltip />}
        <Tooltip
          color="white"
          rootClassName="max-w-[400px]"
          title={
            percentageStats && (
              <div>
                <Text type="secondary" strong className="text-xs">
                  {percentageStats.label}
                </Text>
                {percentageStats.data.length > 0 ? (
                  <Descriptions size="small" column={1} layout="horizontal">
                    {percentageStats.data?.map(({ label, value }) => (
                      <Descriptions.Item label={label} key={label}>
                        {nFormatter(value)}%
                      </Descriptions.Item>
                    ))}
                  </Descriptions>
                ) : (
                  <div className="text-xs">None</div>
                )}
              </div>
            )
          }
        >
          <Flex gap="small" rootClassName="w-max overflow-hidden">
            <Badge
              status="success"
              text={`${nFormatter(barChartProps?.data?.progress?.approved ?? 0)} approved`}
            />
            <Badge
              status="warning"
              text={`${nFormatter(barChartProps?.data?.progress?.classified ?? 0)} classified`}
            />
            <Badge
              status="default"
              text={`${nFormatter(barChartProps?.data?.progress?.unlabeled)} unlabeled`}
            />
          </Flex>
        </Tooltip>
      </div>
    </Flex>
  );
};
