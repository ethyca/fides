import {
  Button,
  ColumnsType,
  Empty,
  Flex,
  formatIsoLocation,
  Icons,
  isoStringToEntry,
  Tag,
} from "fidesui";
import { useRouter } from "next/router";
import React, { useMemo, useState } from "react";

import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { useHasPermission } from "~/features/common/Restrict";
import { TagExpandableCell } from "~/features/common/table/cells";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { EnablePrivacyExperienceCell } from "~/features/privacy-experience/cells";
import { COMPONENT_MAP } from "~/features/privacy-experience/constants";
import { useGetAllExperienceConfigsQuery } from "~/features/privacy-experience/privacy-experience.slice";
import {
  ExperienceConfigListViewResponse,
  PrivacyNoticeRegion,
  ScopeRegistryEnum,
} from "~/types/api";

const EmptyTableExperience = ({ canCreate }: { canCreate: boolean }) => {
  const router = useRouter();
  return (
    <div data-testid="empty-state">
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={
          <Flex vertical gap="small">
            <div>No privacy experiences found.</div>
            {canCreate && (
              <div>
                <Button
                  onClick={() => router.push(`${PRIVACY_EXPERIENCE_ROUTE}/new`)}
                  type="primary"
                  size="small"
                  data-testid="add-privacy-experience-btn"
                  icon={<Icons.Add />}
                  iconPosition="end"
                >
                  Create new experience
                </Button>
              </div>
            )}
          </Flex>
        }
      />
    </div>
  );
};

const getRegionValues = (regions: PrivacyNoticeRegion[] | undefined) => {
  if (!regions) {
    return [];
  }
  return regions.flatMap((region) => {
    const isoEntry = isoStringToEntry(region);
    const label = isoEntry
      ? formatIsoLocation({ isoEntry, showFlag: true })
      : PRIVACY_NOTICE_REGION_RECORD[region];
    if (label === undefined) {
      return [];
    }
    return [{ label, key: region }];
  });
};

const usePrivacyExperiencesTable = () => {
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_EXPERIENCE_UPDATE,
  ]);

  const tableState = useTableState({
    pagination: {
      defaultPageSize: 25,
      pageSizeOptions: [25, 50, 100],
    },
  });

  const { pageIndex, pageSize } = tableState;

  const { data, isLoading, isFetching } = useGetAllExperienceConfigsQuery({
    page: pageIndex,
    size: pageSize,
  });

  const [isLocationsExpanded, setIsLocationsExpanded] = useState(false);
  const [isPropertiesExpanded, setIsPropertiesExpanded] = useState(false);

  const dataSource = useMemo(() => data?.items ?? [], [data?.items]);
  const totalRows = data?.total ?? 0;

  const emptyText = useMemo(
    () => <EmptyTableExperience canCreate={userCanUpdate} />,
    [userCanUpdate],
  );

  const antTableConfig = useMemo(
    () => ({
      dataSource,
      totalRows,
      isLoading,
      isFetching,
      getRowKey: (record: ExperienceConfigListViewResponse) => record.id,
      customTableProps: {
        locale: { emptyText },
      },
    }),
    [dataSource, totalRows, isLoading, isFetching, emptyText],
  );

  const { tableProps } = useAntTable(tableState, antTableConfig);

  const columns: ColumnsType<ExperienceConfigListViewResponse> = useMemo(
    () => [
      {
        title: "Title",
        dataIndex: "name",
        key: "name",
        render: (_, { id, name }) => (
          <LinkCell
            href={
              userCanUpdate ? `${PRIVACY_EXPERIENCE_ROUTE}/${id}` : undefined
            }
          >
            {name}
          </LinkCell>
        ),
      },
      {
        title: "Component",
        dataIndex: "component",
        key: "component",
        render: (_, { component }) => <Tag>{COMPONENT_MAP.get(component)}</Tag>,
      },
      {
        title: "Locations",
        dataIndex: "regions",
        key: "regions",
        render: (_, { regions }) => (
          <TagExpandableCell
            values={getRegionValues(regions)}
            columnState={{ isExpanded: isLocationsExpanded }}
          />
        ),
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e) => {
            e.domEvent.stopPropagation();
            if (e.key === "expand-all") {
              setIsLocationsExpanded(true);
            } else if (e.key === "collapse-all") {
              setIsLocationsExpanded(false);
            }
          },
        },
      },
      {
        title: "Properties",
        dataIndex: "properties",
        key: "properties",
        render: (_, { properties }) => (
          <TagExpandableCell
            values={(properties ?? []).map((p) => ({
              label: p.name,
              key: p.id,
            }))}
            columnState={{ isExpanded: isPropertiesExpanded }}
          />
        ),
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e) => {
            e.domEvent.stopPropagation();
            if (e.key === "expand-all") {
              setIsPropertiesExpanded(true);
            } else if (e.key === "collapse-all") {
              setIsPropertiesExpanded(false);
            }
          },
        },
      },
      {
        title: "Last update",
        dataIndex: "updated_at",
        key: "updated_at",
        render: (_, { updated_at }) => (
          <span>{new Date(updated_at).toDateString()}</span>
        ),
      },
      ...(userCanUpdate
        ? [
            {
              title: "Enable",
              dataIndex: "disabled",
              key: "enable",
              render: (
                _: unknown,
                record: ExperienceConfigListViewResponse,
              ) => <EnablePrivacyExperienceCell record={record} />,
              onCell: () => ({
                onClick: (e: React.MouseEvent) => e.stopPropagation(),
              }),
            },
          ]
        : []),
    ],
    [userCanUpdate, isLocationsExpanded, isPropertiesExpanded],
  );

  return {
    tableProps,
    columns,
    userCanUpdate,
  };
};

export default usePrivacyExperiencesTable;
