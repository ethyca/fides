import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntTag as Tag,
  formatIsoLocation,
  isoStringToEntry,
} from "fidesui";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { useHasPermission } from "~/features/common/Restrict";
import { TagExpandableCell } from "~/features/common/table/cells";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { FRAMEWORK_MAP } from "~/features/privacy-notices/constants";
import { useGetAllPrivacyNoticesQuery } from "~/features/privacy-notices/privacy-notices.slice";
import MechanismCell from "~/features/privacy-notices/table/cells/MechanismCell";
import NoticeChildrenCell from "~/features/privacy-notices/table/cells/NoticeChildrenCell";
import NoticeEnableCell from "~/features/privacy-notices/table/cells/NoticeEnableCell";
import StatusCell from "~/features/privacy-notices/table/cells/StatusCell";
import {
  ConsentMechanism,
  LimitedPrivacyNoticeResponseSchema,
  PrivacyNoticeRegion,
  ScopeRegistryEnum,
} from "~/types/api";

const EmptyTableNotice = () => {
  const router = useRouter();

  return (
    <Empty
      image={Empty.PRESENTED_IMAGE_SIMPLE}
      description={
        <Flex vertical gap="small">
          <div>No privacy notices found.</div>
          <div>
            <Button
              onClick={() => router.push(`${PRIVACY_NOTICES_ROUTE}/new`)}
              type="primary"
              size="small"
              data-testid="add-privacy-notice-btn"
            >
              Add a privacy notice +
            </Button>
          </div>
        </Flex>
      }
    />
  );
};

// we have to alias this because Ant Table automatically sets the "expandable"
// prop on table rows if the data type has a "children" property
interface PrivacyNoticeRowType
  extends Omit<LimitedPrivacyNoticeResponseSchema, "children"> {
  noticeChildren?: LimitedPrivacyNoticeResponseSchema["children"];
}

const usePrivacyNoticesTable = () => {
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_NOTICE_UPDATE,
  ]);

  const tableState = useTableState({
    pagination: {
      defaultPageSize: 25,
      pageSizeOptions: [25, 50, 100],
    },
  });

  const { pageIndex, pageSize } = tableState;

  // Fetch data
  const { data, isLoading, isFetching } = useGetAllPrivacyNoticesQuery({
    page: pageIndex,
    size: pageSize,
  });

  const [isLocationsExpanded, setIsLocationsExpanded] = useState(false);

  const items = useMemo(() => data?.items ?? [], [data?.items]);
  const dataSource: PrivacyNoticeRowType[] = useMemo(
    () =>
      items.map((item) => {
        const { children, ...rest } = item;
        return {
          ...rest,
          noticeChildren: children,
        };
      }),
    [items],
  );

  const totalRows = data?.total ?? 0;

  const antTableConfig = useMemo(
    () => ({
      dataSource,
      totalRows,
      isLoading,
      isFetching,
      getRowKey: (record: PrivacyNoticeRowType) => record.id,
      customTableProps: {
        locale: {
          emptyText: <EmptyTableNotice />,
        },
      },
    }),
    [totalRows, isLoading, isFetching, dataSource],
  );

  const { tableProps } = useAntTable(tableState, antTableConfig);

  const columns: ColumnsType<PrivacyNoticeRowType> = useMemo(
    () =>
      [
        {
          title: "Title",
          dataIndex: "name",
          key: "name",
          render: (_: boolean, record: PrivacyNoticeRowType) => (
            <LinkCell
              href={`${PRIVACY_NOTICES_ROUTE}/${record.id}`}
              data-testid="notice-name"
            >
              {record.name}
            </LinkCell>
          ),
        },
        {
          title: "Mechanism",
          dataIndex: "consent_mechanism",
          key: "consent_mechanism",
          render: (value: ConsentMechanism) => <MechanismCell value={value} />,
        },
        {
          title: "Locations",
          dataIndex: "configured_regions",
          key: "regions",
          render: (regions: PrivacyNoticeRegion[] | undefined) => {
            const values =
              regions?.map((location: PrivacyNoticeRegion) => {
                const isoEntry = isoStringToEntry(location);
                return {
                  label: isoEntry
                    ? formatIsoLocation({ isoEntry, showFlag: true })
                    : (PRIVACY_NOTICE_REGION_RECORD[location] ?? location),
                  key: location,
                };
              }) ?? [];
            return (
              <TagExpandableCell
                values={values}
                columnState={{
                  isExpanded: isLocationsExpanded,
                }}
              />
            );
          },
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
          title: "Status",
          dataIndex: "disabled",
          key: "status",
          render: (_: boolean, record: PrivacyNoticeRowType) => (
            <StatusCell record={record} />
          ),
        },
        {
          title: "Framework",
          dataIndex: "framework",
          key: "framework",
          render: (framework: string | null) =>
            framework ? (
              <Tag data-testid="framework-badge">
                {FRAMEWORK_MAP.get(framework) ?? framework}
              </Tag>
            ) : null,
        },
        {
          title: "Children",
          dataIndex: "noticeChildren",
          key: "noticeChildren",
          render: (noticeChildren?: LimitedPrivacyNoticeResponseSchema[]) => (
            <NoticeChildrenCell value={noticeChildren} />
          ),
        },
        ...(userCanUpdate
          ? [
              {
                title: "Enable",
                dataIndex: "disabled",
                key: "enable",
                render: (_: boolean, record: PrivacyNoticeRowType) => (
                  <NoticeEnableCell record={record} />
                ),
                onCell: () => ({
                  onClick: (e: React.MouseEvent) => e.stopPropagation(),
                }),
              },
            ]
          : []),
      ] as ColumnsType<PrivacyNoticeRowType>,
    [userCanUpdate, isLocationsExpanded],
  );

  return {
    tableProps,
    columns,
    userCanUpdate,
    isEmpty: !isLoading && items.length === 0,
  };
};

export default usePrivacyNoticesTable;
