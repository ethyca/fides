import classNames from "classnames";
import { Button, Divider, DonutChart, Flex, Text, Title } from "fidesui";
import { OpenCloseArrow } from "fidesui";
import { AnimatePresence, motion } from "motion/react";

import { nFormatter } from "~/features/common/utils";
import { AggregateStatisticsResponse } from "~/types/api/models/AggregateStatisticsResponse";

import { getProgressColor } from "./ProgressCard/ProgressCard";
import { MONITOR_TYPE_TO_LABEL } from "./ProgressCard/utils";

export interface MonitorStatsCollapsedProps {
  statistics: AggregateStatisticsResponse[];
  isExpanded: boolean;
  onToggle: () => void;
  activeMonitorType?: string | null;
  /** "horizontal" for top layout, "vertical" for sidebar */
  direction?: "horizontal" | "vertical";
}

/** Crossfade a value: old fades out, new fades in */
const FadeValue = ({ value }: { value: string | number }) => (
  <AnimatePresence mode="wait">
    <motion.span
      key={String(value)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
    >
      {value}
    </motion.span>
  </AnimatePresence>
);

const CollapsedStat = ({
  stat,
  isDimmed,
}: {
  stat: AggregateStatisticsResponse;
  isDimmed: boolean;
}) => {
  const percent = stat.approval_progress?.percentage ?? 0;
  const approved = stat.approval_progress?.approved ?? 0;
  const total = stat.approval_progress?.total ?? 0;
  const hasMonitors = (stat.total_monitors ?? 0) > 0;

  return (
    <motion.div
      animate={{ opacity: isDimmed ? 0.4 : hasMonitors ? 1 : 0.5 }}
      transition={{ duration: 0.35, ease: "easeInOut" }}
    >
      <Flex
        align="center"
        gap="small"
        className={classNames("py-2", isDimmed && "pointer-events-none")}
      >
        <div className="h-9 w-9 flex-none">
          <DonutChart
            centerLabel={
              <Title level={3} rootClassName="!text-[9px]">
                <FadeValue value={`${nFormatter(percent)}%`} />
              </Title>
            }
            variant="thin"
            fit="fill"
            segments={[
              {
                color: getProgressColor(percent),
                value: percent,
              },
              {
                color: "colorPrimaryBg",
                value: 100 - percent,
              },
            ]}
          />
        </div>
        <Flex vertical className="min-w-0">
          <Text strong className="whitespace-nowrap text-xs leading-tight">
            {MONITOR_TYPE_TO_LABEL[stat.monitor_type]}
          </Text>
          <Text type="secondary" className="text-[10px] leading-tight">
            {hasMonitors ? (
              <>
                <FadeValue value={nFormatter(approved)} /> /{" "}
                <FadeValue value={nFormatter(total)} /> approved
              </>
            ) : (
              "No monitors"
            )}
          </Text>
        </Flex>
      </Flex>
    </motion.div>
  );
};

const MonitorStatsCollapsed = ({
  statistics,
  isExpanded,
  onToggle,
  activeMonitorType,
  direction = "vertical",
}: MonitorStatsCollapsedProps) => {
  if (statistics.length === 0) {
    return null;
  }

  const isHorizontal = direction === "horizontal";

  return (
    <Flex
      vertical={!isHorizontal}
      align={isHorizontal ? "center" : undefined}
      gap={isHorizontal ? "middle" : undefined}
      className="w-full"
    >
      {statistics.map((stat, index) => {
        const isDimmed =
          activeMonitorType != null &&
          (stat.monitor_type as string) !== activeMonitorType;

        return (
          <Flex
            key={stat.monitor_type}
            align="center"
            gap={isHorizontal ? "small" : undefined}
          >
            {isHorizontal && index > 0 && (
              <Divider type="vertical" className="!mx-0 h-6" />
            )}
            <CollapsedStat stat={stat} isDimmed={isDimmed} />
          </Flex>
        );
      })}
      {isHorizontal && (
        <div className="ml-auto flex-none">
          <Button
            type="text"
            size="small"
            onClick={onToggle}
            aria-label={isExpanded ? "Collapse stats" : "Expand stats"}
            icon={<OpenCloseArrow isOpen={isExpanded} arrowSize={8} />}
          />
        </div>
      )}
    </Flex>
  );
};

export default MonitorStatsCollapsed;
