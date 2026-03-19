import { ColumnsType, Tag } from "fidesui";
import { useMemo } from "react";

import { useAntTable, useTableState } from "~/features/common/table/hooks";
import {
  POLL_INTERVAL_LABELS,
  PollInterval,
} from "~/features/integrations/configure-query-log/constants";
import {
  QueryLogConfigResponse,
  useGetQueryLogConfigsQuery,
} from "~/features/integrations/configure-query-log/query-log-config.slice";
import QueryLogConfigActionsCell from "~/features/integrations/configure-query-log/QueryLogConfigActionsCell";

enum QueryLogConfigColumnKeys {
  NAME = "name",
  KEY = "key",
  STATUS = "status",
  POLL_INTERVAL = "poll_interval_seconds",
  ACTION = "action",
}

interface UseQueryLogConfigTableConfig {
  integrationKey: string;
  onEdit: (config: QueryLogConfigResponse) => void;
}

export const useQueryLogConfigTable = ({
  integrationKey,
  onEdit,
}: UseQueryLogConfigTableConfig) => {
  const tableState = useTableState<QueryLogConfigColumnKeys>();

  const { pageIndex, pageSize } = tableState;

  const {
    isLoading,
    isFetching,
    data: response,
  } = useGetQueryLogConfigsQuery({
    page: pageIndex,
    size: pageSize,
    connection_config_key: integrationKey,
  });

  const antTableConfig = useMemo(
    () => ({
      enableSelection: false,
      getRowKey: (record: QueryLogConfigResponse) => record.key,
      isLoading,
      isFetching,
      dataSource: response?.items ?? [],
      totalRows: response?.total ?? 0,
    }),
    [isLoading, isFetching, response?.items, response?.total],
  );

  const antTable = useAntTable<
    QueryLogConfigResponse,
    QueryLogConfigColumnKeys
  >(tableState, antTableConfig);

  const columns: ColumnsType<QueryLogConfigResponse> = useMemo(
    () => [
      {
        title: "Status",
        dataIndex: QueryLogConfigColumnKeys.STATUS,
        key: QueryLogConfigColumnKeys.STATUS,
        width: 120,
        render: (_: unknown, record: QueryLogConfigResponse) => (
          <Tag color={record.enabled ? "success" : "default"}>
            {record.enabled ? "Enabled" : "Disabled"}
          </Tag>
        ),
      },
      {
        title: "Poll interval",
        dataIndex: QueryLogConfigColumnKeys.POLL_INTERVAL,
        key: QueryLogConfigColumnKeys.POLL_INTERVAL,
        render: (_: unknown, record: QueryLogConfigResponse) =>
          POLL_INTERVAL_LABELS[record.poll_interval_seconds as PollInterval] ??
          `${record.poll_interval_seconds}s`,
      },
      {
        title: "Actions",
        key: QueryLogConfigColumnKeys.ACTION,
        width: 200,
        render: (_: unknown, record: QueryLogConfigResponse) => (
          <QueryLogConfigActionsCell
            config={record}
            onEdit={() => onEdit(record)}
          />
        ),
        fixed: "right" as const,
      },
    ],
    [onEdit],
  );

  const hasConfig = (response?.items?.length ?? 0) > 0;

  return {
    columns,
    tableProps: antTable.tableProps,
    isLoading,
    isFetching,
    hasConfig,
  };
};
