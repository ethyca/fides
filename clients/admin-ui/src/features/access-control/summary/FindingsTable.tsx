import { Flex, Pagination, Table, Typography } from "fidesui";
import { useMemo } from "react";

import { useGetPolicyViolationsQuery } from "~/features/access-control/access-control.slice";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";

import { getViolationsColumns } from "./violationsColumns";

export const FindingsTable = () => {
  const { paginationProps, pageIndex, pageSize } = useAntPagination({
    pageQueryKey: "findings_page",
    sizeQueryKey: "findings_size",
  });

  const { data, isLoading } = useGetPolicyViolationsQuery({
    page: pageIndex,
    size: pageSize,
  });

  const columns = useMemo(() => getViolationsColumns(), []);

  return (
    <div className="mt-6">
      <Typography.Title level={5} style={{ margin: 0, marginBottom: 16 }}>
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
        onRow={() => ({ style: { cursor: "pointer" }, onClick: () => {} })}
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
