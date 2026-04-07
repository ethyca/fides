import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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
  const [isResetting, setIsResetting] = useState(false);

  // Reset state synchronously during render when actorType changes,
  // preventing a wasted request with the stale page number.
  const prevActorTypeRef = useRef(actorType);
  if (prevActorTypeRef.current !== actorType) {
    prevActorTypeRef.current = actorType;
    setPage(1);
    setAllItems([]);
    setHasMore(true);
    setIsResetting(true);
  }

  // Always poll page 1 for fresh items
  const page1Params = useMemo(
    () => ({
      page: 1,
      size: PAGE_SIZE,
      ...(actorType
        ? { actor_type: actorType as "user" | "system" | "agent" }
        : {}),
    }),
    [actorType],
  );

  const { data: page1Data, isFetching: isFetchingPage1 } =
    useGetActivityFeedQuery(page1Params, {
      pollingInterval: POLLING_INTERVAL,
      skipPollingIfUnfocused: true,
    });

  // Fetch deeper pages on demand (skip when page 1 — already covered above)
  const deepParams = useMemo(
    () => ({
      page,
      size: PAGE_SIZE,
      ...(actorType
        ? { actor_type: actorType as "user" | "system" | "agent" }
        : {}),
    }),
    [page, actorType],
  );

  const { data: deepData, isFetching: isFetchingDeep } =
    useGetActivityFeedQuery(deepParams, { skip: page <= 1 });

  // Process page 1 data (initial load + poll refreshes)
  useEffect(() => {
    if (!page1Data) {
      return;
    }

    setIsResetting(false);

    if (page === 1) {
      setAllItems(page1Data.items);
      setHasMore(page1Data.page < page1Data.pages);
    } else {
      // Poll refresh — prepend genuinely new items
      setAllItems((prev) => {
        const existingIds = new Set(prev.map((i) => i.id));
        const newItems = page1Data.items.filter((i) => !existingIds.has(i.id));
        return newItems.length > 0 ? [...newItems, ...prev] : prev;
      });
    }
  }, [page1Data, page]);

  // Append items from deeper pages
  useEffect(() => {
    if (!deepData || page <= 1) {
      return;
    }

    setAllItems((prev) => {
      const existingIds = new Set(prev.map((i) => i.id));
      const deduped = deepData.items.filter((i) => !existingIds.has(i.id));
      return deduped.length > 0 ? [...prev, ...deduped] : prev;
    });

    setHasMore(deepData.page < deepData.pages);
  }, [deepData, page]);

  const loadMore = useCallback(() => {
    if (!isFetchingDeep && !isFetchingPage1 && hasMore) {
      setPage((prev) => prev + 1);
    }
  }, [isFetchingDeep, isFetchingPage1, hasMore]);

  // Show spinner for initial load, filter resets, or when loading deeper pages,
  // but not during background poll refreshes.
  const isFetching =
    isResetting || (isFetchingPage1 && allItems.length === 0) || isFetchingDeep;

  return {
    items: allItems,
    isFetching,
    hasMore,
    loadMore,
  };
};
