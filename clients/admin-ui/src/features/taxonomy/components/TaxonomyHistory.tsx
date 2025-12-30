import { formatDistance } from "date-fns";
import { Flex, List, Pagination, Skeleton, Tooltip, Typography } from "fidesui";

import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { formatDate, sentenceCase } from "~/features/common/utils";
import { useGetTaxonomyHistoryQuery } from "~/features/taxonomy/taxonomy.slice";

enum EventType {
  USAGE_DELETED = "taxonomy.usage.deleted",
  USAGE_ADDED = "taxonomy.usage.updated",
  ELEMENT_CREATED = "taxonomy.element.created",
  ELEMENT_UPDATED = "taxonomy.element.updated",
  ELEMENT_DELETED = "taxonomy.element.deleted",
  CREATED = "taxonomy.created",
}

const EVENT_TYPE_LABEL_MAP = {
  [EventType.USAGE_DELETED]: "Usage removed",
  [EventType.USAGE_ADDED]: "Usage added",
  [EventType.ELEMENT_CREATED]: "Element created",
  [EventType.ELEMENT_DELETED]: "Element deleted",
  [EventType.ELEMENT_UPDATED]: "Element updated",
  [EventType.CREATED]: "Taxonomy created",
};

const TaxonomyHistory = ({ taxonomyKey }: { taxonomyKey: string }) => {
  const pagination = useAntPagination({
    defaultPageSize: 10,
    disableUrlState: true,
    showSizeChanger: false,
  });
  const { paginationProps, pageIndex, pageSize } = pagination;

  const { data, isLoading } = useGetTaxonomyHistoryQuery({
    fides_key: taxonomyKey,
    page: pageIndex,
    size: pageSize,
  });

  if (isLoading) {
    return (
      <List size="small" itemLayout="vertical">
        {Array.from({ length: 5 }).map((_, index) => (
          // eslint-disable-next-line react/no-array-index-key
          <List.Item key={index}>
            <Skeleton active>
              <List.Item.Meta />
            </Skeleton>
          </List.Item>
        ))}
      </List>
    );
  }

  const dataSource = data?.items ?? [];

  return (
    <Flex vertical gap="middle">
      <List size="small" itemLayout="vertical">
        {dataSource.map((item) => {
          const distance = formatDistance(
            new Date(item.created_at),
            new Date(),
            {
              addSuffix: true,
            },
          );
          const formattedDate = formatDate(new Date(item.created_at));

          const description = (
            <>
              <Tooltip title={formattedDate}>
                {`${sentenceCase(distance)}`}
              </Tooltip>
              {item.user_id ? <span> by {item.user_id}</span> : null}
            </>
          );

          return (
            <List.Item key={item.id}>
              <List.Item.Meta
                title={
                  EVENT_TYPE_LABEL_MAP[item.event_type as EventType] ??
                  item.event_type
                }
                description={description}
              />
              <Typography.Text>{item.description}</Typography.Text>
            </List.Item>
          );
        })}
      </List>
      <Flex justify="middle">
        {data?.total && (
          <Pagination
            {...paginationProps}
            total={data.total}
            hideOnSinglePage
          />
        )}
      </Flex>
    </Flex>
  );
};

export default TaxonomyHistory;
