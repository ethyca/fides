import {
  AntColumnsType as ColumnsType,
  AntTag as Tag,
  formatIsoLocation,
  isoStringToEntry,
} from "fidesui";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { useHasPermission } from "~/features/common/Restrict";
import { TagExpandableCell } from "~/features/common/table/cells";
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

  const items = useMemo(() => data?.items ?? [], [data?.items]);
  const totalRows = data?.total ?? 0;

  // Ant Table integration
  const antTableConfig = useMemo(
    () => ({
      dataSource: items,
      totalRows,
      isLoading,
      isFetching,
      getRowKey: (record: LimitedPrivacyNoticeResponseSchema) => record.id,
    }),
    [items, totalRows, isLoading, isFetching],
  );

  const { tableProps } = useAntTable(tableState, antTableConfig);

  // Columns definition (memoized)
  const columns: ColumnsType<LimitedPrivacyNoticeResponseSchema> = useMemo(
    () =>
      [
        {
          title: "Title",
          dataIndex: "name",
          key: "name",
          render: (name: string) => (
            <span data-testid="notice-name">{name}</span>
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
            return <TagExpandableCell values={values} />;
          },
        },
        {
          title: "Status",
          dataIndex: "disabled",
          key: "status",
          render: (_: boolean, record: LimitedPrivacyNoticeResponseSchema) => (
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
          dataIndex: "children",
          key: "children",
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
                render: (
                  _: boolean,
                  record: LimitedPrivacyNoticeResponseSchema,
                ) => <NoticeEnableCell record={record} />,
                onCell: () => ({
                  onClick: (e: React.MouseEvent) => e.stopPropagation(),
                }),
              },
            ]
          : []),
      ] as ColumnsType<LimitedPrivacyNoticeResponseSchema>,
    [userCanUpdate],
  );

  return {
    tableProps,
    columns,
    userCanUpdate,
    isEmpty: !isLoading && items.length === 0,
  };
};

export default usePrivacyNoticesTable;
