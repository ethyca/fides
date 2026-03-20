import { Flex, Spin, Table } from "fidesui";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useGetViolationLogsQuery } from "../access-control.slice";
import type { PolicyViolationLog } from "../types";
import { getRequestLogColumns } from "./requestLogColumns";
import { useRequestLogFilterContext } from "./useRequestLogFilters";

const columns = getRequestLogColumns();

const getRowKey = (record: PolicyViolationLog) => record.id;

const HIGHLIGHT_DURATION_MS = 1500;
const LIVE_TAIL_POLL_MS = 5000;
const PAGE_SIZE = 25;

interface RequestLogTableProps {
  onRowClick?: (record: PolicyViolationLog) => void;
}

export const RequestLogTable = ({ onRowClick }: RequestLogTableProps) => {
  const { filters, liveTail } = useRequestLogFilterContext();
  const [cursor, setCursor] = useState<string | null>(null);
  const [allItems, setAllItems] = useState<PolicyViolationLog[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());
  const knownIdsRef = useRef<Set<string>>(new Set());

  const queryParams = useMemo(
    () => ({
      ...(cursor ? { cursor } : {}),
      size: PAGE_SIZE,
      ...filters,
    }),
    [cursor, filters],
  );

  const { data, isFetching } = useGetViolationLogsQuery(queryParams, {
    pollingInterval: liveTail ? LIVE_TAIL_POLL_MS : 0,
  });

  useEffect(() => {
    setCursor(null);
    setAllItems([]);
    setHasMore(true);
    knownIdsRef.current = new Set();
  }, [filters]);

  useEffect(() => {
    if (!data) {
      return;
    }

    let cleanupTimer: (() => void) | undefined;

    if (cursor === null) {
      if (liveTail && knownIdsRef.current.size > 0) {
        const newIds = new Set(
          data.items
            .filter((item) => !knownIdsRef.current.has(item.id))
            .map((item) => item.id),
        );
        if (newIds.size > 0) {
          setHighlightedIds(newIds);
          const timer = setTimeout(
            () => setHighlightedIds(new Set()),
            HIGHLIGHT_DURATION_MS,
          );
          cleanupTimer = () => clearTimeout(timer);
        }
      }
      setAllItems(data.items);
    } else {
      setAllItems((prev) => [...prev, ...data.items]);
    }

    for (const item of data.items) {
      knownIdsRef.current.add(item.id);
    }
    setHasMore(data.next_cursor !== null);

    return cleanupTimer;
  }, [data, cursor, liveTail]);

  const loadMore = useCallback(() => {
    if (!isFetching && hasMore && data?.next_cursor) {
      setCursor(data.next_cursor);
    }
  }, [isFetching, hasMore, data?.next_cursor]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      { threshold: 0.1 },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  return (
    <div className="flex max-h-[calc(100vh-48px)] flex-col overflow-auto">
      <style>{`
        .live-tail-row td {
          background-color: rgb(254 243 199) !important;
          transition: background-color 1.5s ease-out;
        }
        .live-tail-row-faded td {
          transition: background-color 1.5s ease-out;
        }
      `}</style>
      <Table
        dataSource={allItems}
        columns={columns}
        pagination={false}
        bordered={false}
        rowKey={getRowKey}
        onRow={(record) => ({
          onClick: () => onRowClick?.(record),
          className: [
            onRowClick ? "cursor-pointer" : "",
            highlightedIds.has(record.id) ? "live-tail-row" : "",
          ]
            .filter(Boolean)
            .join(" "),
        })}
        size="small"
        sticky
      />
      <div ref={sentinelRef} className="h-px shrink-0" />
      {isFetching && (
        <Flex justify="center" className="py-4">
          <Spin size="small" />
        </Flex>
      )}
    </div>
  );
};
