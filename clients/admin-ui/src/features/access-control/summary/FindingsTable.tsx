import { Flex, Pagination, Table, Typography } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo } from "react";

import { useGetPolicyViolationsQuery } from "~/features/access-control/access-control.slice";
import type { PolicyViolationAggregate } from "~/features/access-control/types";
import { ACCESS_CONTROL_REQUEST_LOG_ROUTE } from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";

import { getViolationsColumns } from "./violationsColumns";

export const FindingsTable = () => {
  const router = useRouter();
  const { paginationProps, pageIndex, pageSize } = useAntPagination({
    pageQueryKey: "findings_page",
    sizeQueryKey: "findings_size",
  });

  const { data, isLoading } = useGetPolicyViolationsQuery({
    page: pageIndex,
    size: pageSize,
  });

  const columns = useMemo(() => getViolationsColumns(), []);

  const handleRowClick = useCallback(
    (record: PolicyViolationAggregate) => {
      router.push({
        pathname: ACCESS_CONTROL_REQUEST_LOG_ROUTE,
        query: { policy: record.policy },
      });
    },
    [router],
  );

  return (
    <div className="mt-6">
      <Typography.Title level={5} className="!m-0 !mb-4">
        Findings
      </Typography.Title>
      <Table
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        pagination={false}
        rowKey={(record) => `${record.policy}-${record.control}`}
        size="small"
        bordered={false}
        onRow={(record) => ({
          style: { cursor: "pointer" },
          onClick: () => handleRowClick(record),
        })}
      />
      {(data?.total ?? 0) > 0 && (
        <Flex justify="end" className="mt-4">
          <Pagination
            {...paginationProps}
            total={data?.total}
            showTotal={(t, range) => `${range[0]}-${range[1]} of ${t} items`}
          />
        </Flex>
      )}
    </div>
  );
};
