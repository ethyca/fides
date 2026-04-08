import classNames from "classnames";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { Avatar, Card, Flex, Icons, Spin, Text } from "fidesui";
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
    case "user":
      return <Icons.User size={12} />;
    case "system":
      return <Icons.Settings size={12} />;
    default:
      return undefined;
  }
};

const FeedItemContent = ({ item }: { item: ActivityFeedItem }) => {
  const attribution = item.event_source
    ? `via ${EVENT_SOURCE_LABELS[item.event_source] ?? item.event_source}`
    : undefined;

  return (
    <Flex align="center" gap={8}>
      <Avatar
        icon={getActorIcon(item.actor_type)}
        size={22}
        className={styles.actorIcon}
      />
      <Text ellipsis style={{ flex: 1, minWidth: 0 }}>
        {item.message}
        {attribution && (
          <span className={styles.attributionText}> {attribution}</span>
        )}
      </Text>
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
        {isFetching && items.length === 0 ? (
          <Flex justify="center" align="center" className="h-full">
            <Spin size="small" />
          </Flex>
        ) : !isFetching && items.length === 0 ? (
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
      </div>
    </Card>
  );
};
