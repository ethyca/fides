import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import type { CarbonIconType } from "@carbon/icons-react";
import { Avatar, Card, Flex, Icons, Segmented, Spin, Text } from "fidesui";
import { motion } from "motion/react";
import NextLink from "next/link";
import { useEffect, useRef, useState } from "react";

import { usePrefersReducedMotion } from "~/features/common/hooks";
import {
  ACTION_CTA,
  ACTIVITY_FILTER_OPTIONS,
  EVENT_SOURCE_LABELS,
} from "~/features/dashboard/constants";
import type { ActivityFeedItem } from "~/features/dashboard/types";

import styles from "./ActivityFeedCard.module.scss";
import { useInfiniteActivityFeed } from "./useInfiniteActivityFeed";

dayjs.extend(relativeTime);

const ACTOR_ICONS: Record<string, CarbonIconType> = {
  user: Icons.User,
  system: Icons.Settings,
  agent: Icons.Activity,
};

const FeedItemContent = ({ item }: { item: ActivityFeedItem }) => {
  const attribution = item.event_source
    ? `via ${EVENT_SOURCE_LABELS[item.event_source] ?? item.event_source}`
    : undefined;

  return (
    <Flex align="center" gap={12}>
      <Avatar
        icon={
          ACTOR_ICONS[item.actor_type]
            ? (() => {
                const Icon = ACTOR_ICONS[item.actor_type];
                return <Icon size={14} />;
              })()
            : undefined
        }
        size={28}
        className={styles.actorIcon}
      />
      <Flex vertical flex={1} style={{ minWidth: 0 }}>
        <Text ellipsis>{item.message}</Text>
        {attribution && (
          <Text className={styles.attributionText}>{attribution}</Text>
        )}
      </Flex>
      <Text type="secondary" style={{ fontSize: "var(--ant-font-size-sm)", flexShrink: 0 }}>
        {dayjs(item.timestamp).fromNow()}
      </Text>
    </Flex>
  );
};

export const ActivityFeedCard = () => {
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const reduceMotion = usePrefersReducedMotion();
  const sentinelRef = useRef<HTMLDivElement>(null);

  const actorType = activeFilter === "all" ? undefined : activeFilter;
  const { items, isFetching, hasMore, loadMore } = useInfiniteActivityFeed({
    actorType,
  });

  // IntersectionObserver for infinite scroll
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && items.length > 0) {
          loadMore();
        }
      },
      { threshold: 0.1 },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore, items.length]);

  const motionProps = reduceMotion
    ? {}
    : {
        initial: { opacity: 0, y: 8 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.2, ease: "easeOut" as const },
      };

  return (
    <Card
      variant="borderless"
      title="Activity"
      extra={
        <Segmented
          size="small"
          options={ACTIVITY_FILTER_OPTIONS.map((opt) => ({
            label: opt.label,
            value: opt.value,
          }))}
          value={activeFilter}
          onChange={(val) => setActiveFilter(val as string)}
        />
      }
      className={styles.cardContainer}
    >
      <div className={styles.scrollContainer}>
        {items.map((item) => {
          const cta =
            item.event_type && ACTION_CTA[item.event_type]
              ? ACTION_CTA[item.event_type]
              : null;
          const href = cta
            ? cta.route(item.action_data ?? {})
            : null;

          return (
            <motion.div key={item.id} {...motionProps}>
              {href ? (
                <NextLink href={href} className={styles.feedItem + " " + styles.clickable}>
                  <FeedItemContent item={item} />
                </NextLink>
              ) : (
                <div className={styles.feedItem + " " + styles.nonClickable}>
                  <FeedItemContent item={item} />
                </div>
              )}
            </motion.div>
          );
        })}
        {hasMore && <div ref={sentinelRef} className="h-px shrink-0" />}
        {isFetching && (
          <Flex justify="center" style={{ padding: 12 }}>
            <Spin size="small" />
          </Flex>
        )}
      </div>
    </Card>
  );
};
