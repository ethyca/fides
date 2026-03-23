import { Flex, Spin, Table } from "fidesui";
import { useEffect, useRef } from "react";

import { useInfiniteViolationLogs } from "./hooks/useInfiniteViolationLogs";
import { useRequestLogFilterContext } from "./hooks/useRequestLogFilters";
import { getRequestLogColumns } from "./requestLogColumns";
import type { PolicyViolationLog } from "./types";

const columns = getRequestLogColumns();

const getRowKey = (record: PolicyViolationLog) => record.id;

interface RequestLogTableProps {
  onRowClick?: (record: PolicyViolationLog) => void;
}

export const RequestLogTable = ({ onRowClick }: RequestLogTableProps) => {
  const { filters, liveTail } = useRequestLogFilterContext();
  const { items, isFetching, highlightedIds, loadMore } =
    useInfiniteViolationLogs({ filters, liveTail });

  const sentinelRef = useRef<HTMLDivElement>(null);

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
    <Flex vertical className="max-h-[calc(100vh-48px)] overflow-auto">
      <Table
        dataSource={items}
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
    </Flex>
  );
};
