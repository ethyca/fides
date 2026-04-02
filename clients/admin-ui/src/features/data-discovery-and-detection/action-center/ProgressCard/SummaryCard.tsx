import { antTheme, Descriptions, Flex, Text, Tooltip } from "fidesui";
import { AnimatePresence, motion } from "motion/react";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";
import { nFormatter, pluralize } from "~/features/common/utils";
import { AggregateStatisticsResponse } from "~/types/api/models/AggregateStatisticsResponse";

// fidesui palette tokens (not exported as JS, using hex directly)
const PALETTE_INFO = "#4a90e2"; // classified (blue)

export const SUMMARY_CARD_LABELS: Record<string, string> = {
  datastore: "Monitored data stores",
  infrastructure: "Monitored infrastructure",
  website: "Monitored websites",
};

const RESOURCE_NOUN: Record<string, string> = {
  datastore: "resources",
  infrastructure: "systems",
  website: "resources",
};

const MONITOR_TYPE_TO_CLASSIFICATION_LABEL: Record<string, string> = {
  datastore: "Data categories",
  infrastructure: "Data uses",
  website: "Categories of consent",
};

const MONITOR_TYPE_TO_CLASSIFICATION_KEY: Record<string, string> = {
  datastore: "data_categories",
  infrastructure: "data_uses",
  website: "data_uses",
};

export interface SummaryCardProps {
  stat: AggregateStatisticsResponse;
}

/** Crossfade a value: old fades out, new fades in */
const FadeValue = ({
  value,
  className,
  style,
}: {
  value: string | number;
  className?: string;
  style?: React.CSSProperties;
}) => (
  <AnimatePresence mode="wait">
    <motion.span
      key={String(value)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
      className={className}
      style={style}
    >
      {value}
    </motion.span>
  </AnimatePresence>
);

const SummaryCard = ({ stat }: SummaryCardProps) => {
  const { token } = antTheme.useToken();

  const approved = stat.approval_progress?.approved ?? 0;
  const total = stat.approval_progress?.total ?? 0;
  const sc = stat.status_counts ?? {};
  const classified =
    (sc.classified ?? 0) + (sc.reviewed ?? 0) + (sc.classifying ?? 0);
  const detected = (sc.addition ?? 0) + (sc.removal ?? 0);
  const needReview = classified + detected;

  // Progress bar percentages — approved fills remaining space so the bar is
  // always full when there are any resources. Goal: get it all green.
  const classifiedPct = total > 0 ? (classified / total) * 100 : 0;
  const detectedPct = total > 0 ? (detected / total) * 100 : 0;
  const approvedPct = total > 0 ? 100 - classifiedPct - detectedPct : 0;

  const title = SUMMARY_CARD_LABELS[stat.monitor_type] ?? stat.monitor_type;
  const resourceNoun = RESOURCE_NOUN[stat.monitor_type] ?? "resources";
  const monitorCount = stat.total_monitors ?? 0;

  const relativeTime = useRelativeTime(
    stat.last_updated ? new Date(stat.last_updated) : new Date(),
  );

  // Type-specific status breakdown for "need review" tooltip
  const vc = stat.vendor_counts;
  const statusBreakdown = (() => {
    switch (stat.monitor_type) {
      case "infrastructure":
        return [
          vc?.known && { label: "Known vendors", count: vc.known },
          vc?.unknown && { label: "Unknown vendors", count: vc.unknown },
        ];
      case "website":
        return [
          classified > 0 && { label: "Categorized", count: classified },
          detected > 0 && { label: "Uncategorized", count: detected },
        ];
      default:
        return [
          sc.classified && { label: "Classified", count: sc.classified },
          sc.addition && { label: "Unlabeled", count: sc.addition },
          sc.classifying && { label: "Classifying", count: sc.classifying },
          sc.reviewed && { label: "In review", count: sc.reviewed },
        ];
    }
  })().filter(Boolean) as { label: string; count: number }[];

  // Classifications for "classified" tooltip
  const classificationKey =
    MONITOR_TYPE_TO_CLASSIFICATION_KEY[stat.monitor_type];
  const classificationLabel =
    MONITOR_TYPE_TO_CLASSIFICATION_LABEL[stat.monitor_type];
  const classifications =
    stat.top_classifications?.[
      classificationKey as keyof typeof stat.top_classifications
    ] ?? [];

  const classifiedTooltipContent =
    classifications.length > 0 ? (
      <Flex vertical gap={2}>
        <Text strong className="text-xs">
          {classificationLabel}
        </Text>
        <Descriptions size="small" column={1} layout="horizontal">
          {classifications.map(
            (item: { name: string; percentage: number }) => (
              <Descriptions.Item label={item.name} key={item.name}>
                {nFormatter(item.percentage)}%
              </Descriptions.Item>
            ),
          )}
        </Descriptions>
      </Flex>
    ) : null;

  return (
    <Flex vertical gap={8} className="w-full py-2">
      {/* Header */}
      <Flex justify="space-between" align="baseline">
        <Text strong>{title}</Text>
        <Tooltip title={`Updated: ${relativeTime}`}>
          <Text type="secondary" className="cursor-default text-[10px]">
            {relativeTime}
          </Text>
        </Tooltip>
      </Flex>

      {/* Hero number — tooltip appears above the number */}
      <Tooltip
        color="white"
        placement="topLeft"
        title={
          statusBreakdown.length > 0 ? (
            <Descriptions size="small" column={1} layout="horizontal">
              {statusBreakdown.map(({ label, count }) => (
                <Descriptions.Item label={label} key={label}>
                  {nFormatter(count)}
                </Descriptions.Item>
              ))}
            </Descriptions>
          ) : null
        }
      >
        <div className="cursor-default py-1" style={{ width: "fit-content" }}>
          <Text
            strong
            className="text-3xl leading-none"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            <FadeValue value={nFormatter(needReview)} />
          </Text>
          <div>
            <Text type="secondary" className="text-xs">
              {needReview > 0
                ? `${resourceNoun} need review across ${monitorCount} ${pluralize(monitorCount, "monitor", "monitors")}`
                : total > 0
                  ? `All ${resourceNoun} approved across ${monitorCount} ${pluralize(monitorCount, "monitor", "monitors")}`
                  : `No ${resourceNoun} detected yet`}
            </Text>
          </div>
        </div>
      </Tooltip>

      {/* Stacked progress bar */}
      <div className="flex h-2 w-full overflow-hidden rounded-sm bg-gray-100">
        <div
          className="transition-all duration-1000 ease-in-out"
          style={{
            width: `${approvedPct}%`,
            backgroundColor: token.colorSuccess,
          }}
        />
        <Tooltip color="white" placement="bottom" title={classifiedTooltipContent}>
          <div
            className="cursor-default transition-all duration-1000 ease-in-out"
            style={{
              width: `${classifiedPct}%`,
              backgroundColor: PALETTE_INFO,
            }}
          />
        </Tooltip>
        <div
          className="transition-all duration-1000 ease-in-out"
          style={{
            width: `${detectedPct}%`,
            backgroundColor: token.colorTextQuaternary,
          }}
        />
      </div>

      {/* Key with counts */}
      <Flex gap="middle">
        <Flex align="center" gap={6}>
          <div
            className="h-2 w-2 flex-none rounded-full"
            style={{ backgroundColor: token.colorSuccess }}
          />
          <Text className="text-xs">
            <FadeValue value={nFormatter(approved)} /> approved
          </Text>
        </Flex>
        <Tooltip color="white" placement="bottom" title={classifiedTooltipContent}>
          <Flex align="center" gap={6} className="cursor-default">
            <div
              className="h-2 w-2 flex-none rounded-full"
              style={{ backgroundColor: PALETTE_INFO }}
            />
            <Text className="text-xs">
              <FadeValue value={nFormatter(classified)} /> classified
            </Text>
          </Flex>
        </Tooltip>
        <Flex align="center" gap={6}>
          <div
            className="h-2 w-2 flex-none rounded-full"
            style={{ backgroundColor: token.colorTextQuaternary }}
          />
          <Text className="text-xs">
            <FadeValue value={nFormatter(detected)} /> unlabeled
          </Text>
        </Flex>
      </Flex>
    </Flex>
  );
};

export default SummaryCard;
