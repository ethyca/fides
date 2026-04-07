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
      ...(actorType
        ? { actor_type: actorType as "user" | "system" }
        : {}),
    }),
    [page, actorType],
  );

  const { data, isFetching } = useGetActivityFeedQuery(queryParams, {
    pollingInterval: POLLING_INTERVAL,
    skipPollingIfUnfocused: true,
    refetchOnMountOrArgChange: true,
  });

  useEffect(() => {
    setPage(1);
  }, [actorType]);

  useEffect(() => {
    if (!data) {
      setAllItems([]);
      setHasMore(true);
      return;
    }

    if (page === 1) {
      setAllItems(data.items);
    } else {
      setAllItems((prev) => {
        const existingIds = new Set(prev.map((i) => i.id));
        const deduped = data.items.filter((i) => !existingIds.has(i.id));
        return deduped.length > 0 ? [...prev, ...deduped] : prev;
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
