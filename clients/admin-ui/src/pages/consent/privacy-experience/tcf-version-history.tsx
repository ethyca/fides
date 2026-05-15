import { formatDistance } from "date-fns";
import { Button, Flex, Table, Typography, useMessage } from "fidesui";
import { useMemo } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { usePagination } from "~/features/common/hooks";
import PageHeader from "~/features/common/PageHeader";
import { InfinitePaginator } from "~/features/common/pagination/InfinitePaginator";
import {
  TCFVersionHashHistoryResponse,
  useGetTCFVersionHistoryQuery,
} from "~/features/consent-reporting/consent-reporting.slice";

const TCFVersionHistoryPage = () => {
  const pagination = usePagination();
  const { pageIndex, pageSize, updatePageIndex } = pagination;
  const message = useMessage();

  const { data, isLoading, isFetching, refetch } = useGetTCFVersionHistoryQuery(
    { page: pageIndex, size: pageSize },
  );

  const items = useMemo(() => data?.items ?? [], [data]);

  const handleClickRefresh = async () => {
    updatePageIndex(1);
    await refetch();
    message.success("TCF version history refreshed successfully.");
  };

  const columns = useMemo(
    () => [
      {
        title: "Changed at",
        dataIndex: "changed_at",
        key: "changed_at",
        width: 160,
        render: (value: string) =>
          formatDistance(new Date(value), new Date(), { addSuffix: true }),
      },
      {
        title: "Current hash",
        dataIndex: "current_hash",
        key: "current_hash",
        render: (value: string) => (
          <Typography.Text ellipsis={{ tooltip: value }}>
            {value}
          </Typography.Text>
        ),
      },
      {
        title: "Previous hash",
        dataIndex: "previous_hash",
        key: "previous_hash",
        render: (value: string | null | undefined) =>
          value ? (
            <Typography.Text ellipsis={{ tooltip: value }}>
              {value}
            </Typography.Text>
          ) : (
            "—"
          ),
      },
      {
        title: "Config ID",
        dataIndex: "tcf_configuration_id",
        key: "tcf_configuration_id",
        render: (value: string | null | undefined) =>
          value ? (
            <Typography.Text ellipsis={{ tooltip: value }}>
              {value}
            </Typography.Text>
          ) : (
            "—"
          ),
      },
      {
        title: "Trigger source",
        dataIndex: "trigger_source",
        key: "trigger_source",
      },
    ],
    [],
  );

  return (
    <FixedLayout title="TCF version history">
      <PageHeader
        heading="TCF version history"
        rightContent={
          <Button
            type="primary"
            onClick={handleClickRefresh}
            loading={isFetching}
          >
            Refresh
          </Button>
        }
      />
      <Flex vertical gap="medium">
        <Table<TCFVersionHashHistoryResponse>
          columns={columns}
          dataSource={items}
          rowKey="id"
          loading={isLoading}
          pagination={false}
          data-testid="tcf-version-history-table"
          tableLayout="fixed"
        />
        <InfinitePaginator
          disableNext={(data?.items?.length ?? 0) < pageSize}
          pagination={pagination}
        />
      </Flex>
    </FixedLayout>
  );
};

export default TCFVersionHistoryPage;
