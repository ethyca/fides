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

import { DATA_CONSUMERS_NEW_ROUTE } from "~/features/common/nav/routes";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";

import { CONSUMER_TYPE_LABELS, DataConsumerType } from "./constants";
import {
  DataConsumer,
  useGetAllDataConsumersQuery,
} from "./data-consumer.slice";
import DataConsumerActionsCell from "./DataConsumerActionsCell";

const useDataConsumersTable = () => {
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

  const { data, error, isLoading, isFetching } = useGetAllDataConsumersQuery({
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
      getRowKey: (record: DataConsumer) => record.id,
      customTableProps: {
        locale: {
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Flex vertical gap="small" align="center">
                  <Typography.Paragraph>
                    No data consumers found.
                  </Typography.Paragraph>
                  <Flex>
                    <Button
                      type="primary"
                      onClick={() => router.push(DATA_CONSUMERS_NEW_ROUTE)}
                    >
                      Add data consumer
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

  const columns: ColumnsType<DataConsumer> = useMemo(
    () => [
      {
        title: "Name",
        dataIndex: "name",
        key: "name",
        render: (_, { name, id }) => (
          <LinkCell href={`/data-consumers/${id}`}>{name}</LinkCell>
        ),
      },
      {
        title: "Type",
        dataIndex: "type",
        key: "type",
        render: (_, { type }) => (
          <Tag>{CONSUMER_TYPE_LABELS[type as DataConsumerType] ?? type}</Tag>
        ),
      },
      {
        title: "Contact",
        dataIndex: "contact_email",
        key: "contact_email",
        render: (_, { contact_email }) => contact_email || "N/A",
      },
      {
        title: "Purposes",
        dataIndex: "purpose_fides_keys",
        key: "purpose_fides_keys",
        render: (_, { purpose_fides_keys }) =>
          purpose_fides_keys && purpose_fides_keys.length > 0 ? (
            <Space size={[0, 4]} wrap>
              {purpose_fides_keys.map((key) => (
                <Tag key={key}>{key}</Tag>
              ))}
            </Space>
          ) : (
            "N/A"
          ),
      },
      {
        title: "Tags",
        dataIndex: "tags",
        key: "tags",
        render: (_, { tags }) =>
          tags && tags.length > 0 ? (
            <Space size={[0, 4]} wrap>
              {tags.map((tag) => (
                <Tag key={tag}>{tag}</Tag>
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
        render: (_, consumer) => (
          <DataConsumerActionsCell consumer={consumer} />
        ),
      },
    ],
    [],
  );

  return { tableProps, columns, error, searchQuery, updateSearch };
};

export default useDataConsumersTable;
