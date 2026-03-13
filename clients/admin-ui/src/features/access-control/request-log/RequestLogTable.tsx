import { Flex, Spin, Table } from "fidesui";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useGetPolicyViolationLogsQuery } from "../access-control.slice";
import type { PolicyViolationLog } from "../types";
import { getRequestLogColumns } from "./requestLogColumns";

const columns = getRequestLogColumns();

const getRowKey = (record: PolicyViolationLog) => record.id;

const HIGHLIGHT_DURATION_MS = 1500;

interface RequestLogTableProps {
  filters: Record<string, string | string[] | undefined>;
  liveTailItems?: PolicyViolationLog[];
  onRowClick?: (record: PolicyViolationLog) => void;
}

const PAGE_SIZE = 25;

export const RequestLogTable = ({
  filters,
  liveTailItems = [],
  onRowClick,
}: RequestLogTableProps) => {
  const [page, setPage] = useState(1);
  const [allItems, setAllItems] = useState<PolicyViolationLog[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());

  const queryParams = useMemo(
    () => ({
      page,
      size: PAGE_SIZE,
      ...filters,
    }),
    [page, filters],
  );

  const { data, isFetching } = useGetPolicyViolationLogsQuery(queryParams);

  useEffect(() => {
    setPage(1);
    setAllItems([]);
    setHasMore(true);
  }, [filters]);

  useEffect(() => {
    if (!data || data.page !== page) {
      return;
    }
    if (page === 1) {
      setAllItems(data.items);
    } else {
      setAllItems((prev) => [...prev, ...data.items]);
    }
    setHasMore(page < data.pages);
  }, [data, page]);

  const prevLiveTailCountRef = useRef(0);

  useEffect(() => {
    const prevCount = prevLiveTailCountRef.current;
    const newCount = liveTailItems.length;
    prevLiveTailCountRef.current = newCount;

    const addedCount = newCount - prevCount;
    if (addedCount <= 0) {
      return undefined;
    }

    const newIds = new Set(
      liveTailItems.slice(0, addedCount).map((item) => item.id),
    );
    setHighlightedIds(newIds);

    const timer = setTimeout(() => {
      setHighlightedIds(new Set());
    }, HIGHLIGHT_DURATION_MS);

    return () => clearTimeout(timer);
  }, [liveTailItems]);

  const dataSource = useMemo(
    () => [...liveTailItems, ...allItems],
    [liveTailItems, allItems],
  );

  const loadMore = useCallback(() => {
    if (!isFetching && hasMore) {
      setPage((prev) => prev + 1);
    }
  }, [isFetching, hasMore]);

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
    <div className="sticky top-0 z-10 flex max-h-[calc(100vh-48px)] flex-col overflow-auto">
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
        dataSource={dataSource}
        columns={columns}
        pagination={false}
        bordered={false}
        rowKey={getRowKey}
        onRow={(record) => ({
          onClick: () => onRowClick?.(record),
          className: [
            onRowClick ? "cursor-pointer" : "",
            highlightedIds.has(record.id)
              ? "live-tail-row"
              : record.id.startsWith("live-")
                ? "live-tail-row-faded"
                : "",
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
