import classNames from "classnames";
import {
  Card,
  Descriptions,
  Divider,
  DonutChart,
  Flex,
  Paragraph,
  TagList,
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
}

const getProgressColor = (percent: number) => {
  switch (true) {
    case percent > 80:
      return "colorSuccess";
    case percent > 60:
      return "colorWarning";
    default:
      return "colorErrorTextHover";
  }
};

export const ProgressCard = ({
  title,
  subtitle,
  progress,
  numericStats,
  percentageStats,
  lastUpdated,
  compact,
}: PropsWithChildren<ProgressCardProps>) => {
  const relativeTime = useRelativeTime(
    lastUpdated ? new Date(lastUpdated) : new Date(),
  );

  return (
    <Card
      size="small"
      rootClassName={classNames(
        compact ? "w-full" : "h-full overflow-hidden w-full",
      )}
      classNames={{
        body: "h-full overflow-hidden",
      }}
      title={
        !compact && (
          <Flex justify="space-between" align="baseline">
            <span>{title}</span>
            <Text type="secondary" className="text-xs !font-normal">
              {subtitle}
            </Text>
          </Flex>
        )
      }
    >
      <div
        className={classNames(
          `grid overflow-hidden w-full gap-2 xl:gap-4`,
          compact
            ? "grid-cols-[1fr,min-content,1fr,min-content,1fr]"
            : "grid-cols-1 xl:grid-cols-[auto,1fr,1fr]",
        )}
      >
        <Flex
          vertical={!compact}
          className={classNames([
            "gap-0 xl:gap-1",
            !compact && "content-center justify-center text-center",
          ])}
        >
          <div
            className={classNames(compact ? "h-full" : "min-h-[80px] w-full")}
          >
            <DonutChart
              centerLabel={
                <Title
                  level={compact ? 3 : 5}
                  rootClassName={compact ? "!text-xs" : ""}
                >{`${nFormatter(progress.percent)}%`}</Title>
              }
              variant={compact ? "thin" : "default"}
              fit={compact ? "fill" : "contain"}
              segments={[
                {
                  color: getProgressColor(progress.percent ?? 0),
                  value: progress.percent ?? 0,
                },
                {
                  color: "colorPrimaryBg",
                  value: 100 - (progress.percent ?? 0),
                },
              ]}
            />
          </div>
          <Flex
            vertical
            justify={compact ? "center" : undefined}
            className="w-full"
          >
            <Text
              type="secondary"
              strong={compact}
              className={compact ? "whitespace-nowrap text-xs" : undefined}
            >
              {progress.label}
            </Text>
            <Text strong>
              {nFormatter(progress.numerator)} of{" "}
              {nFormatter(progress.denominator)}
            </Text>
          </Flex>
        </Flex>
        <div
          className={classNames(
            "grid grid-cols-1 grid-rows-[1fr,min-content,1fr,min-content] col-span-2 gap-2",
            !!compact && "contents",
          )}
        >
          {numericStats && (
            <>
              {compact && (
                <Divider
                  size="small"
                  rootClassName="!m-0 !my-0 h-full"
                  vertical={compact}
                />
              )}
              <div>
                <Text type="secondary" strong className="text-xs">
                  {numericStats.label}
                </Text>
                <Paragraph
                  type="secondary"
                  className="!my-0 !text-xs"
                  ellipsis={{
                    rows: 1,
                    tooltip: {
                      color: "white",
                      title: (
                        <Descriptions
                          size="small"
                          column={1}
                          layout="horizontal"
                        >
                          {numericStats.data?.map(({ label, count }) => (
                            <Descriptions.Item label={label} key={label}>
                              {nFormatter(count)}
                            </Descriptions.Item>
                          ))}
                        </Descriptions>
                      ),
                    },
                  }}
                >
                  {numericStats.data.length > 0
                    ? numericStats.data
                        ?.map(
                          ({ label, count }) => `${nFormatter(count)} ${label}`,
                        )
                        .join(", ")
                    : "None"}
                </Paragraph>
              </div>
            </>
          )}
          {percentageStats && (
            <>
              <Divider
                size="small"
                rootClassName="!m-0 !my-0 h-full"
                vertical={compact}
              />
              <div>
                <Text type="secondary" strong className="text-xs">
                  {percentageStats.label}
                </Text>
                {percentageStats.data.length > 0 ? (
                  <Tooltip
                    color="white"
                    styles={{
                      root: {
                        maxWidth: 400,
                      },
                    }}
                    title={
                      <Descriptions size="small" column={1} layout="horizontal">
                        {percentageStats.data?.map(({ label, value }) => (
                          <Descriptions.Item label={label} key={label}>
                            {nFormatter(value)}%
                          </Descriptions.Item>
                        ))}
                      </Descriptions>
                    }
                  >
                    <span>
                      <TagList
                        maxTags={undefined}
                        className="flex flex-nowrap gap-1"
                        tags={percentageStats.data?.map(({ label, value }) => ({
                          label: (
                            <span>{`${nFormatter(value)}% ${label}`}</span>
                          ),
                          value: `${value}%`,
                        }))}
                      />
                    </span>
                  </Tooltip>
                ) : (
                  <div className="text-xs">None</div>
                )}
              </div>
            </>
          )}
          <Paragraph
            type="secondary"
            className={classNames(
              "text-xs w-full text-right self-end !my-0",
              !!compact && "hidden",
            )}
            ellipsis={{
              rows: 1,
              tooltip: { title: <>Updated: {relativeTime}</> },
            }}
          >
            <>Updated: {relativeTime}</>
          </Paragraph>
        </div>
      </div>
    </Card>
  );
};
