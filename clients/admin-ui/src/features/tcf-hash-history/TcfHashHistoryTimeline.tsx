import { format } from "date-fns";
import {
  Alert,
  Empty,
  Flex,
  Icons,
  Skeleton,
  Tag,
  Timeline,
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

import {
  TRIGGER_SOURCE_COLORS,
  TRIGGER_SOURCE_DOT_COLORS,
  TRIGGER_SOURCE_LABELS,
} from "./constants";
import TcfHashDisplay from "./TcfHashDisplay";

interface Props {
  experienceConfigId: string;
}

const TcfHashHistoryTimeline = ({ experienceConfigId }: Props) => {
  const pagination = usePagination();
  const { pageIndex, pageSize } = pagination;

  const { data, isLoading, isError } =
    useGetExperienceConfigTCFHashHistoryQuery({
      experienceConfigId,
      page: pageIndex,
      size: pageSize,
    });

  const timelineItems = useMemo(() => {
    if (!data?.items) {
      return [];
    }
    return data.items.map((entry: TCFVersionHashHistoryResponse) => ({
      color:
        TRIGGER_SOURCE_DOT_COLORS[entry.trigger_source] ??
        "var(--fidesui-neutral-400)",
      children: (
        <Flex vertical gap="small" className="pb-2">
          <Flex align="center" gap="small" wrap="wrap">
            <Tag
              color={TRIGGER_SOURCE_COLORS[entry.trigger_source] ?? "default"}
            >
              {TRIGGER_SOURCE_LABELS[entry.trigger_source] ??
                entry.trigger_source}
            </Tag>
            <Tooltip title={format(new Date(entry.changed_at), "PPpp")}>
              <Typography.Text type="secondary" className="text-xs">
                {format(new Date(entry.changed_at), "dd MMM yyyy, HH:mm")}
              </Typography.Text>
            </Tooltip>
          </Flex>
          <Flex align="center" gap="small">
            <TcfHashDisplay value={entry.previous_hash} />
            <Typography.Text type="secondary">→</Typography.Text>
            <TcfHashDisplay value={entry.current_hash} />
          </Flex>
        </Flex>
      ),
    }));
  }, [data]);

  if (isLoading) {
    return (
      <Flex vertical gap="middle">
        <Skeleton active paragraph={{ rows: 3 }} />
        <Skeleton active paragraph={{ rows: 3 }} />
        <Skeleton active paragraph={{ rows: 3 }} />
      </Flex>
    );
  }

  if (isError) {
    return <Alert type="error" title="Failed to load TCF hash history" />;
  }

  if (!timelineItems.length) {
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
      <Timeline items={timelineItems} data-testid="tcf-hash-history-timeline" />
      <InfinitePaginator
        disableNext={(data?.items?.length ?? 0) < pageSize}
        pagination={pagination}
      />
    </Flex>
  );
};

export default TcfHashHistoryTimeline;
