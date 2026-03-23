import { Table } from "fidesui";
import { useCallback, useMemo } from "react";

import { useGetPolicyViolationsQuery } from "~/features/access-control/access-control.slice";
import { useRequestLogFilterContext } from "~/features/access-control/hooks/useRequestLogFilters";
import type { PolicyViolationAggregate } from "~/features/access-control/types";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";

import { getViolationsColumns } from "./violationsColumns";

interface FindingsTableProps {
  onRowClick?: (record: PolicyViolationAggregate) => void;
}

export const FindingsTable = ({ onRowClick }: FindingsTableProps) => {
  const { filters } = useRequestLogFilterContext();
  const { pageIndex, pageSize } = useAntPagination({
    pageQueryKey: "findings_page",
    sizeQueryKey: "findings_size",
  });

  const { data, isLoading } = useGetPolicyViolationsQuery({
    ...filters,
    page: pageIndex,
    size: pageSize,
  });

  const columns = useMemo(() => getViolationsColumns(), []);

  const handleRowClick = useCallback(
    (record: PolicyViolationAggregate) => {
      onRowClick?.(record);
    },
    [onRowClick],
  );

  return (
    <Table
      columns={columns}
      dataSource={data?.items}
      loading={isLoading}
      rowKey={(record) => `${record.policy}-${record.control}`}
      size="small"
      bordered={false}
      onRow={(record) => ({
        className: onRowClick ? "cursor-pointer" : undefined,
        onClick: onRowClick ? () => handleRowClick(record) : undefined,
      })}
    />
  );
};
