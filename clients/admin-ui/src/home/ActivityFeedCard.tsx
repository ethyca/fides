import classNames from "classnames";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { Avatar, Card, Flex, Icons, SparkleIcon, Spin, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import NextLink from "next/link";
import { useEffect, useRef, useState } from "react";

import {
  ACTION_CTA,
  ACTIVITY_FILTER_OPTIONS,
  EVENT_SOURCE_LABELS,
} from "~/features/dashboard/constants";
import type { ActivityFeedItem } from "~/features/dashboard/types";

import styles from "./ActivityFeedCard.module.scss";
import { useInfiniteActivityFeed } from "./useInfiniteActivityFeed";

dayjs.extend(relativeTime);

const getActorIcon = (actorType: string) => {
  switch (actorType) {
    case "agent":
      return <SparkleIcon size={14} />;
    case "user":
      return <Icons.User size={14} />;
    case "system":
      return <Icons.Settings size={14} />;
    default:
      return undefined;
  }
};

const getActorIconStyle = (
  actorType: string,
): React.CSSProperties | undefined => {
  if (actorType === "agent") {
    return {
      color: palette.FIDESUI_TERRACOTTA,
      borderColor: palette.FIDESUI_TERRACOTTA,
    };
  }
  return undefined;
};

const FeedItemContent = ({ item }: { item: ActivityFeedItem }) => {
  const attribution = item.event_source
    ? `via ${EVENT_SOURCE_LABELS[item.event_source] ?? item.event_source}`
    : undefined;

  return (
    <Flex align="center" gap={12}>
      <Avatar
        icon={getActorIcon(item.actor_type)}
        size={28}
        className={styles.actorIcon}
        style={getActorIconStyle(item.actor_type)}
      />
      <Flex vertical flex={1} style={{ minWidth: 0 }}>
        <Text ellipsis>{item.message}</Text>
        {attribution && (
          <Text className={styles.attributionText}>{attribution}</Text>
        )}
      </Flex>
      <Text type="secondary" className={styles.timestampText}>
        {dayjs(item.timestamp).fromNow()}
      </Text>
    </Flex>
  );
};

export const ActivityFeedCard = () => {
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const sentinelRef = useRef<HTMLDivElement>(null);

  const actorType = activeFilter === "all" ? undefined : activeFilter;
  const { items, isFetching, hasMore, loadMore } = useInfiniteActivityFeed({
    actorType,
  });

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

  return (
    <Card
      title="Activity"
      variant="borderless"
      tabList={ACTIVITY_FILTER_OPTIONS.map((opt) => ({
        key: opt.value,
        label: opt.label,
      }))}
      activeTabKey={activeFilter}
      onTabChange={setActiveFilter}
      className={styles.cardContainer}
    >
      <div className={styles.scrollContainer}>
        {!isFetching && items.length === 0 ? (
          <Flex
            vertical
            align="center"
            justify="center"
            className={styles.emptyState}
          >
            <Text type="secondary">
              {activeFilter === "all"
                ? "No activity yet"
                : `No ${ACTIVITY_FILTER_OPTIONS.find((o) => o.value === activeFilter)?.label.toLowerCase()} activity`}
            </Text>
          </Flex>
        ) : (
          <>
            {items.map((item) => {
              const cta =
                item.event_type && ACTION_CTA[item.event_type]
                  ? ACTION_CTA[item.event_type]
                  : null;
              const href = cta ? cta.route(item.action_data ?? {}) : null;

              return (
                <div key={item.id}>
                  {href ? (
                    <NextLink
                      href={href}
                      className={classNames(styles.feedItem, styles.clickable)}
                    >
                      <FeedItemContent item={item} />
                    </NextLink>
                  ) : (
                    <div
                      className={classNames(
                        styles.feedItem,
                        styles.nonClickable,
                      )}
                    >
                      <FeedItemContent item={item} />
                    </div>
                  )}
                </div>
              );
            })}
            {hasMore && <div ref={sentinelRef} className="h-px shrink-0" />}
          </>
        )}
        {isFetching && (
          <Flex justify="center" align="center" className="h-full">
            <Spin size="small" />
          </Flex>
        )}
      </div>
    </Card>
  );
};
