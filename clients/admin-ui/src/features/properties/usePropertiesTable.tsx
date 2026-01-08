import { Button, ColumnsType, Empty, Flex } from "fidesui";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { ADD_PROPERTY_ROUTE } from "~/features/common/nav/routes";
import { TagExpandableCell } from "~/features/common/table/cells";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { buildExpandCollapseMenu } from "~/features/data-discovery-and-detection/action-center/utils/columnBuilders";
import { useGetAllPropertiesQuery } from "~/features/properties/property.slice";
import PropertyActionsCell from "~/features/properties/PropertyActionsCell";
import { Property } from "~/types/api";

const usePropertiesTable = () => {
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

  const [isExperiencesExpanded, setIsExperiencesExpanded] = useState(false);
  const [experiencesVersion, setExperiencesVersion] = useState(0);

  const { pageIndex, pageSize, searchQuery, updateSearch } = tableState;

  const { data, error, isLoading, isFetching } = useGetAllPropertiesQuery({
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
      getRowKey: (record: Property) => record.id ?? "",
      locale: {
        emptyText: (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Flex vertical gap="small">
                <div>No properties found.</div>
                <div>
                  <Button
                    type="primary"
                    onClick={() => router.push(ADD_PROPERTY_ROUTE)}
                  >
                    Add a property
                  </Button>
                </div>
              </Flex>
            }
            data-testid="no-results-notice"
          />
        ),
      },
    }),
    [totalRows, isLoading, isFetching, items, router],
  );

  const { tableProps } = useAntTable(tableState, antTableConfig);

  const columns: ColumnsType<Property> = useMemo(
    () => [
      {
        title: "Name",
        dataIndex: "name",
        key: "name",
        render: (_, { name, id }) => (
          <LinkCell href={`/properties/${id}`}>{name}</LinkCell>
        ),
      },
      {
        title: "Type",
        dataIndex: "type",
        key: "type",
      },
      {
        title: "Experiences",
        dataIndex: "experiences",
        key: "experiences",
        render: (_, { experiences }) => (
          <TagExpandableCell
            values={experiences.map((experience) => ({
              label: experience.name,
              key: experience.id,
            }))}
            columnState={{
              isExpanded: isExperiencesExpanded,
              version: experiencesVersion,
            }}
          />
        ),
        menu: buildExpandCollapseMenu(
          setIsExperiencesExpanded,
          setExperiencesVersion,
        ),
      },
      {
        title: "Actions",
        dataIndex: "actions",
        key: "actions",
        render: (_, property) => <PropertyActionsCell property={property} />,
      },
    ],
    [isExperiencesExpanded, experiencesVersion],
  );

  return { tableProps, columns, error, searchQuery, updateSearch };
};

export default usePropertiesTable;
