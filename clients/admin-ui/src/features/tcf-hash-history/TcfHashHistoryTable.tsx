import { format } from "date-fns";
import {
  Empty,
  Flex,
  Icons,
  Skeleton,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "fidesui";
import { useMemo } from "react";

import { usePagination } from "~/features/common/hooks";
import { InfinitePaginator } from "~/features/common/pagination/InfinitePaginator";
import {
  TCFVersionHashHistoryResponse,
  useGetExperienceConfigTCFHashHistoryQuery,
} from "~/features/privacy-experience/privacy-experience.slice";

import { TRIGGER_SOURCE_COLORS, TRIGGER_SOURCE_LABELS } from "./constants";

interface Props {
  experienceConfigId: string;
}

const HashCell = ({ value }: { value: string | null | undefined }) =>
  value ? (
    <Tooltip title={value}>
      <Typography.Text code className="text-xs">
        {value.slice(0, 8)}
      </Typography.Text>
    </Tooltip>
  ) : (
    <Typography.Text type="secondary" className="text-xs">
      (none)
    </Typography.Text>
  );

const columns = [
  {
    title: "Date",
    dataIndex: "changed_at",
    key: "changed_at",
    render: (value: string) => (
      <Tooltip title={format(new Date(value), "PPpp")}>
        <Typography.Text className="text-xs">
          {format(new Date(value), "dd MMM yyyy, HH:mm")}
        </Typography.Text>
      </Tooltip>
    ),
  },
  {
    title: "Trigger",
    dataIndex: "trigger_source",
    key: "trigger_source",
    render: (value: string) => (
      <Tag color={TRIGGER_SOURCE_COLORS[value] ?? "default"}>
        {TRIGGER_SOURCE_LABELS[value] ?? value}
      </Tag>
    ),
  },
  {
    title: "Previous hash",
    dataIndex: "previous_hash",
    key: "previous_hash",
    render: (value: string | null | undefined) => <HashCell value={value} />,
  },
  {
    title: "Current hash",
    dataIndex: "current_hash",
    key: "current_hash",
    render: (value: string | null | undefined) => <HashCell value={value} />,
  },
];

const TcfHashHistoryTable = ({ experienceConfigId }: Props) => {
  const pagination = usePagination();
  const { pageIndex, pageSize } = pagination;

  const { data, isLoading } = useGetExperienceConfigTCFHashHistoryQuery({
    experienceConfigId,
    page: pageIndex,
    size: pageSize,
  });

  const entries = useMemo(() => data?.items ?? [], [data]);

  if (isLoading) {
    return (
      <Flex vertical gap="middle">
        <Skeleton active paragraph={{ rows: 3 }} />
        <Skeleton active paragraph={{ rows: 3 }} />
        <Skeleton active paragraph={{ rows: 3 }} />
      </Flex>
    );
  }

  if (!entries.length) {
    return (
      <Empty
        image={<Icons.Time size={40} color="var(--fidesui-neutral-300)" />}
        imageStyle={{ height: "auto" }}
        description={
          <Flex vertical gap="small" align="center">
            <Typography.Text strong>
              No hash changes recorded yet
            </Typography.Text>
            <Typography.Text type="secondary" className="max-w-sm text-center">
              Hash changes are captured automatically whenever this TCF
              experience configuration is updated. They will appear here once
              the first change is made.
            </Typography.Text>
          </Flex>
        }
      />
    );
  }

  return (
    <Flex vertical gap="middle">
      <Table<TCFVersionHashHistoryResponse>
        columns={columns}
        dataSource={entries}
        rowKey="id"
        pagination={false}
        data-testid="tcf-hash-history-table"
        size="small"
      />
      <InfinitePaginator
        disableNext={(data?.items?.length ?? 0) < pageSize}
        pagination={pagination}
      />
    </Flex>
  );
};

export default TcfHashHistoryTable;
