import { Empty, Flex, Icons, List, Skeleton, Typography } from "fidesui";
import { useMemo } from "react";

import { usePagination } from "~/features/common/hooks";
import { InfinitePaginator } from "~/features/common/pagination/InfinitePaginator";
import {
  TCFVersionHashHistoryResponse,
  useGetExperienceConfigTCFHashHistoryQuery,
} from "~/features/privacy-experience/privacy-experience.slice";

import TcfHashHistoryEntry from "./TcfHashHistoryEntry";

interface Props {
  experienceConfigId: string;
}

const TcfHashHistoryTimeList = ({ experienceConfigId }: Props) => {
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
      <List
        className="!border-none"
        split={false}
        data-testid="tcf-hash-history-timeline"
      >
        <ul className="!list-none">
          {entries.map((entry: TCFVersionHashHistoryResponse) => (
            <li key={entry.id}>
              <TcfHashHistoryEntry entry={entry} />
            </li>
          ))}
        </ul>
      </List>
      <InfinitePaginator
        disableNext={(data?.items?.length ?? 0) < pageSize}
        pagination={pagination}
      />
    </Flex>
  );
};

export default TcfHashHistoryTimeList;
