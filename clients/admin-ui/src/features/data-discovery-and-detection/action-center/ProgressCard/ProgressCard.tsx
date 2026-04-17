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
import { PropsWithChildren, ReactNode } from "react";

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

/**
 * A single badge rendered along the bottom of the card.
 * `status` uses Ant Design's Badge semantic colors:
 *   success (green), warning (yellow), error (red), processing (blue),
 *   default (grey).
 */
export type ProgressCardBadge = {
  status: "success" | "warning" | "error" | "processing" | "default";
  label: string;
  count: number;
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
  /**
   * Primary statistic rendered above the bar chart. Defaults to the sum of
   * `classified + unlabeled` progress buckets for backward compatibility with
   * the Action Center's original "resources needing review" framing. Provide
   * this when the consumer uses a different framing (e.g. Request Manager
   * renders the overdue count as the headline stat).
   */
  primaryStatValue?: number;
  /**
   * Sentence rendered immediately below the primary statistic. Defaults to
   * "resources need review across {subtitle}" (omits the "across" clause in
   * compact mode). Provide this to customize the domain noun (e.g. "requests
   * open — X active") without forking the component.
   */
  progressSummary?: ReactNode;
  /**
   * Override the row of bottom badges. When omitted, the component renders
   * the original Action Center triad of Approved / Classified / Unlabeled
   * pulled from `barChartProps.data.progress`. Provide this when the
   * underlying data uses a different vocabulary (e.g. SLA health with
   * on-track / approaching / overdue buckets).
   */
  badges?: ProgressCardBadge[];
  /**
   * Optional content rendered inside an Ant Tooltip that wraps the card
   * title. Used by consumers that want to surface the card's data model
   * (e.g. which underlying statuses flow into an SLA bucket) without
   * expanding the visible chrome.
   */
  titleTooltip?: ReactNode;
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
  primaryStatValue,
  progressSummary,
  badges,
  titleTooltip,
}: PropsWithChildren<ProgressCardProps>) => {
  const relativeTime = useRelativeTime(
    lastUpdated ? new Date(lastUpdated) : new Date(),
  );

  // Default headline stat mirrors the original Action Center framing:
  // "resources needing review" = classified + unlabeled buckets in the bar chart.
  const defaultStatValue =
    (barChartProps?.data?.progress?.classified ?? 0) +
    (barChartProps?.data?.progress?.unlabeled ?? 0);
  const resolvedStatValue = primaryStatValue ?? defaultStatValue;

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
          {titleTooltip ? (
            <Tooltip
              color="white"
              rootClassName="max-w-[400px]"
              title={titleTooltip}
            >
              {/* Dotted underline + help cursor signal to the user that
                  hovering the title reveals supplementary info. */}
              <Title
                level={5}
                className="cursor-help whitespace-nowrap underline decoration-dotted underline-offset-4"
              >
                {title}
              </Title>
            </Tooltip>
          ) : (
            <Title level={5} className="whitespace-nowrap">
              {title}
            </Title>
          )}
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
        dataSource={[resolvedStatValue]}
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
      {progressSummary ?? (
        <Text>resources need review{!compact && <> across {subtitle}</>}</Text>
      )}
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
            {badges
              ? badges.map((badge) => (
                  <Badge
                    key={`${badge.status}-${badge.label}`}
                    status={badge.status}
                    text={`${nFormatter(badge.count)} ${badge.label}`}
                  />
                ))
              : [
                  <Badge
                    key="approved"
                    status="success"
                    text={`${nFormatter(barChartProps?.data?.progress?.approved ?? 0)} approved`}
                  />,
                  <Badge
                    key="classified"
                    status="warning"
                    text={`${nFormatter(barChartProps?.data?.progress?.classified ?? 0)} classified`}
                  />,
                  <Badge
                    key="unlabeled"
                    status="default"
                    text={`${nFormatter(barChartProps?.data?.progress?.unlabeled)} unlabeled`}
                  />,
                ]}
          </Flex>
        </Tooltip>
      </div>
    </Flex>
  );
};
