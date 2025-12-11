import { formatDistance } from "date-fns";
import {
  AntFlex,
  AntList,
  AntPagination as Pagination,
  AntSkeleton,
  AntTooltip,
  AntTypography,
} from "fidesui";

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
      <AntList size="small" itemLayout="vertical">
        {Array.from({ length: 5 }).map((_, index) => (
          // eslint-disable-next-line react/no-array-index-key
          <AntList.Item key={index}>
            <AntSkeleton active>
              <AntList.Item.Meta />
            </AntSkeleton>
          </AntList.Item>
        ))}
      </AntList>
    );
  }

  return (
    <AntFlex vertical gap="middle">
      <AntList size="small" itemLayout="vertical">
        {data?.items.map((item) => {
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
              <AntTooltip title={formattedDate}>
                {`${sentenceCase(distance)}`}
              </AntTooltip>
              {item.user_id ? <span> by {item.user_id}</span> : null}
            </>
          );

          return (
            <AntList.Item key={item.id}>
              <AntList.Item.Meta
                title={EVENT_TYPE_LABEL_MAP[item.event_type as EventType]}
                description={description}
              />
              <AntTypography.Text>{item.description}</AntTypography.Text>
            </AntList.Item>
          );
        })}
      </AntList>
      <AntFlex justify="middle">
        {data?.total && (
          <Pagination
            {...paginationProps}
            total={data.total}
            hideOnSinglePage
          />
        )}
      </AntFlex>
    </AntFlex>
  );
};

export default TaxonomyHistory;
