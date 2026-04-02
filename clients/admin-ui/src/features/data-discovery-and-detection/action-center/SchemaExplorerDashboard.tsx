import { antTheme, Divider, Flex, Icons, Text } from "fidesui";
import Link from "next/link";
import { AnimatePresence, motion } from "motion/react";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";
import {
  EDIT_SYSTEM_ROUTE,
  INTEGRATION_DETAIL_ROUTE,
} from "~/features/common/nav/routes";
import { nFormatter } from "~/features/common/utils";
import { AggregateStatisticsResponse } from "~/types/api/models/AggregateStatisticsResponse";

import { useGetMonitorConfigQuery } from "./action-center.slice";

const RESOURCE_NOUN: Record<string, string> = {
  datastore: "resources",
  infrastructure: "systems",
  website: "resources",
};

const SECTION_2_HEADER = "Classification";

const CLASSIFICATION_SECTION_LABEL: Record<string, string> = {
  datastore: "Categories",
  infrastructure: "Data uses",
  website: "Consent categories",
};

const CLASSIFICATION_KEY: Record<string, string> = {
  datastore: "data_categories",
  infrastructure: "data_uses",
  website: "data_uses",
};

/** Crossfade a value */
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

/**
 * Status types with labels matching the tag system and corresponding
 * Ant Design token colors for the dots.
 */
const STATUS_CONFIG: {
  key: string;
  label: string;
  tokenColor: string;
}[] = [
  { key: "monitored", label: "Approved", tokenColor: "colorSuccess" },
  { key: "classified", label: "Classified", tokenColor: "#4a90e2" },
  { key: "reviewed", label: "Reviewed", tokenColor: "#7b4ea9" },
  { key: "addition", label: "Unlabeled", tokenColor: "colorTextQuaternary" },
  { key: "removal", label: "Removed", tokenColor: "colorError" },
  { key: "muted", label: "Ignored", tokenColor: "colorTextTertiary" },
  { key: "__error", label: "Error", tokenColor: "colorError" },
];

interface SchemaExplorerDashboardProps {
  stat: AggregateStatisticsResponse;
  monitorId: string;
}

const SchemaExplorerDashboard = ({
  stat,
  monitorId,
}: SchemaExplorerDashboardProps) => {
  const { token } = antTheme.useToken();
  const { data: monitorConfig } = useGetMonitorConfigQuery({
    monitor_config_id: monitorId,
  });

  const approved = stat.approval_progress?.approved ?? 0;
  const total = stat.approval_progress?.total ?? 0;
  const sc = stat.status_counts ?? {};
  const classified =
    (sc.classified ?? 0) + (sc.reviewed ?? 0) + (sc.classifying ?? 0);
  const detected = (sc.addition ?? 0) + (sc.removal ?? 0);
  const needReview = classified + detected;

  const classifiedPct = total > 0 ? (classified / total) * 100 : 0;
  const detectedPct = total > 0 ? (detected / total) * 100 : 0;
  const approvedPct = total > 0 ? 100 - classifiedPct - detectedPct : 0;

  const resourceNoun = RESOURCE_NOUN[stat.monitor_type] ?? "resources";

  // Monitor details
  const connectionKey = monitorConfig?.connection_config_key;
  const monitorName = monitorConfig?.name ?? monitorId;
  const integrationHref = connectionKey
    ? INTEGRATION_DETAIL_ROUTE.replace("[id]", connectionKey)
    : undefined;
  const systemHref = connectionKey
    ? EDIT_SYSTEM_ROUTE.replace("[id]", connectionKey)
    : undefined;
  const lastMonitored = monitorConfig?.last_monitored;
  const scanTime = useRelativeTime(
    lastMonitored ? new Date(lastMonitored) : new Date(),
  );

  // Show all statuses — even those with 0 count
  const scAny = sc as Record<string, number | undefined>;
  const statusItems = STATUS_CONFIG.map(({ key, label, tokenColor }) => {
    const count =
      key === "__error"
        ? (scAny.classification_error ?? 0) + (scAny.promotion_error ?? 0)
        : scAny[key] ?? 0;
    return { label, count, tokenColor };
  });


  return (
    <Flex className="w-full py-2" align="stretch">
      {/* Section 1: Progress */}
      <Flex vertical gap={6} className="min-w-0 flex-1 pr-4">
        <Flex vertical className="cursor-default">
          <Text
            strong
            className="text-2xl leading-none"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            <FadeValue value={nFormatter(needReview)} />
          </Text>
          <Text type="secondary" className="mt-1 text-xs">
            {needReview > 0
              ? `${resourceNoun} need review`
              : total > 0
                ? `All ${resourceNoun} approved`
                : `No ${resourceNoun} detected yet`}
          </Text>
        </Flex>

        <div className="flex h-2 w-full overflow-hidden rounded-sm bg-gray-100">
          <div
            className="transition-all duration-1000 ease-in-out"
            style={{
              width: `${approvedPct}%`,
              backgroundColor: token.colorSuccess,
            }}
          />
          <div
            className="transition-all duration-1000 ease-in-out"
            style={{
              width: `${classifiedPct}%`,
              backgroundColor: "#4a90e2", // fidesui palette: info
            }}
          />
          <div
            className="transition-all duration-1000 ease-in-out"
            style={{
              width: `${detectedPct}%`,
              backgroundColor: token.colorTextQuaternary,
            }}
          />
        </div>
      </Flex>

      <Divider type="vertical" className="!mx-0 !h-auto self-stretch" />

      {/* Section 2: Classification */}
      <div className="min-w-0 flex-1 px-4">
        <Text strong className="mb-2 block text-xs">
          {SECTION_2_HEADER}
        </Text>
        <div className="mb-1">
          <Text type="secondary" className="text-xs">
            Status:{" "}
          </Text>
          <Text className="text-xs">
            {statusItems
              .filter(({ count }) => count > 0)
              .map(({ label, count }) => `${nFormatter(count)} ${label.toLowerCase()}`)
              .join(", ")}
          </Text>
        </div>
        {(() => {
          const key = CLASSIFICATION_KEY[stat.monitor_type];
          const items = (
            stat.top_classifications?.[
              key as keyof typeof stat.top_classifications
            ] ?? []
          ) as { name: string; percentage: number }[];
          if (items.length === 0) return null;
          const label = CLASSIFICATION_SECTION_LABEL[stat.monitor_type];
          return (
            <div className="truncate">
              <Text type="secondary" className="text-xs">
                {label}:{" "}
              </Text>
              <Text className="text-xs">
                {items
                  .map((item) => `${item.name} (${nFormatter(item.percentage)}%)`)
                  .join(", ")}
              </Text>
            </div>
          );
        })()}
      </div>

      <Divider type="vertical" className="!mx-0 !h-auto self-stretch" />

      {/* Section 3: Details */}
      <div className="min-w-0 flex-1 pl-4">
        <Text strong className="mb-2 block text-xs">
          Details
        </Text>
        {connectionKey && (
          <div className="mb-1">
            <Text type="secondary" className="text-xs">
              System:{" "}
            </Text>
            <Link href={systemHref!} passHref legacyBehavior>
              <a className="group inline-flex items-center gap-1 text-xs font-medium text-[#2b2e35] no-underline hover:underline">
                {connectionKey}
                <Icons.Launch size={12} className="flex-none opacity-0 transition-opacity group-hover:opacity-100" />
              </a>
            </Link>
          </div>
        )}
        {connectionKey && (
          <div>
            <Text type="secondary" className="text-xs">
              Integration:{" "}
            </Text>
            <Link href={integrationHref!} passHref legacyBehavior>
              <a className="group inline-flex items-center gap-1 text-xs font-medium text-[#2b2e35] no-underline hover:underline">
                {monitorName}
                <Icons.Launch size={12} className="flex-none opacity-0 transition-opacity group-hover:opacity-100" />
              </a>
            </Link>
          </div>
        )}
      </div>
    </Flex>
  );
};

export default SchemaExplorerDashboard;
