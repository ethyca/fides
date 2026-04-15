import {
  Button,
  ColumnsType,
  Empty,
  Flex,
  Space,
  Tag,
  Typography,
} from "fidesui";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { DATA_PURPOSES_NEW_ROUTE } from "~/features/common/nav/routes";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import {
  DataPurpose,
  useGetAllDataPurposesQuery,
} from "~/features/data-purposes/data-purpose.slice";
import DataPurposeActionsCell from "~/features/data-purposes/DataPurposeActionsCell";

const useDataPurposesTable = () => {
  const router = useRouter();

  const tableState = useTableState({
    pagination: {
      defaultPageSize: 25,
      pageSizeOptions: [25, 50, 100],
    },
    search: {
      defaultSearchQuery: "",
    },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch } = tableState;

  const { data, error, isLoading, isFetching } = useGetAllDataPurposesQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
  });

  const items = useMemo(() => data?.items ?? [], [data?.items]);
  const totalRows = data?.total ?? 0;

  const antTableConfig = useMemo(
    () => ({
      dataSource: items,
      totalRows,
      isLoading,
      isFetching,
      getRowKey: (record: DataPurpose) => record.fides_key,
      customTableProps: {
        locale: {
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Flex vertical gap="small" align="center">
                  <Typography.Paragraph>
                    No purposes found.
                  </Typography.Paragraph>
                  <Flex>
                    <Button
                      type="primary"
                      onClick={() => router.push(DATA_PURPOSES_NEW_ROUTE)}
                    >
                      Add purpose
                    </Button>
                  </Flex>
                </Flex>
              }
              data-testid="no-results-notice"
            />
          ),
        },
      },
    }),
    [totalRows, isLoading, isFetching, items, router],
  );

  const { tableProps } = useAntTable(tableState, antTableConfig);

  const columns: ColumnsType<DataPurpose> = useMemo(
    () => [
      {
        title: "Name",
        dataIndex: "name",
        key: "name",
        render: (_, { name, fides_key }) => (
          <LinkCell href={`/data-purposes/${fides_key}`}>{name}</LinkCell>
        ),
      },
      {
        title: "Key",
        dataIndex: "fides_key",
        key: "fides_key",
      },
      {
        title: "Data use",
        dataIndex: "data_use",
        key: "data_use",
        render: (_, { data_use }) => <Tag>{data_use}</Tag>,
      },
      {
        title: "Categories",
        dataIndex: "data_categories",
        key: "data_categories",
        render: (_, { data_categories }) =>
          data_categories && data_categories.length > 0 ? (
            <Space size={[0, 4]} wrap>
              {data_categories.map((cat) => (
                <Tag key={cat}>{cat}</Tag>
              ))}
            </Space>
          ) : (
            "N/A"
          ),
      },
      {
        title: "Actions",
        dataIndex: "actions",
        key: "actions",
        render: (_, purpose) => <DataPurposeActionsCell purpose={purpose} />,
      },
    ],
    [],
  );

  return { tableProps, columns, error, searchQuery, updateSearch };
};

export default useDataPurposesTable;
