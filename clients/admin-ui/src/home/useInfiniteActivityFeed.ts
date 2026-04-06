import { useCallback, useEffect, useMemo, useState } from "react";

import { useGetActivityFeedQuery } from "~/features/dashboard/dashboard.slice";
import type { ActivityFeedItem } from "~/features/dashboard/types";

const PAGE_SIZE = 15;
const POLLING_INTERVAL = 30_000;

interface UseInfiniteActivityFeedOptions {
  actorType?: string;
}

export const useInfiniteActivityFeed = ({
  actorType,
}: UseInfiniteActivityFeedOptions) => {
  const [page, setPage] = useState(1);
  const [allItems, setAllItems] = useState<ActivityFeedItem[]>([]);
  const [hasMore, setHasMore] = useState(true);

  const queryParams = useMemo(
    () => ({
      page,
      size: PAGE_SIZE,
      ...(actorType ? { actor_type: actorType as "user" | "system" | "agent" } : {}),
    }),
    [page, actorType],
  );

  const { data, isFetching } = useGetActivityFeedQuery(queryParams, {
    pollingInterval: POLLING_INTERVAL,
  });

  useEffect(() => {
    setPage(1);
    setAllItems([]);
    setHasMore(true);
  }, [actorType]);

  // actorType is in deps so this re-runs on filter switch even when
  // RTK Query returns the same cached data reference.
  useEffect(() => {
    if (!data) {
      return;
    }

    const newItems = actorType
      ? data.items.filter((item) => item.actor_type === actorType)
      : data.items;

    if (page === 1) {
      setAllItems(newItems);
    } else {
      setAllItems((prev) => {
        const existingIds = new Set(prev.map((item) => item.id));
        const deduped = newItems.filter((item) => !existingIds.has(item.id));
        return [...prev, ...deduped];
      });
    }

    setHasMore(data.page < data.pages);
  }, [data, page, actorType]);

  const loadMore = useCallback(() => {
    if (!isFetching && hasMore) {
      setPage((prev) => prev + 1);
    }
  }, [isFetching, hasMore]);

  return {
    items: allItems,
    isFetching,
    hasMore,
    loadMore,
  };
};
