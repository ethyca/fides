import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntFlex as Flex,
  AntTable as Table,
  AntTag as Tag,
  AntTooltip as Tooltip,
  CUSTOM_TAG_COLOR,
  formatIsoLocation,
  isoStringToEntry,
  VStack,
} from "fidesui";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { useHasPermission } from "~/features/common/Restrict";
import { TagExpandableCell } from "~/features/common/table/cells";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { EnableCell } from "~/features/common/table/v2/cells";
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import {
  FRAMEWORK_MAP,
  MECHANISM_MAP,
} from "~/features/privacy-notices/constants";
import {
  useGetAllPrivacyNoticesQuery,
  useLimitedPatchPrivacyNoticesMutation,
} from "~/features/privacy-notices/privacy-notices.slice";
import {
  ConsentMechanism,
  LimitedPrivacyNoticeResponseSchema,
  PrivacyNoticeRegion,
  ScopeRegistryEnum,
} from "~/types/api";

const EmptyTableNotice = () => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="no-results-notice"
    alignSelf="center"
    margin="auto"
  >
    <VStack>
      <span style={{ fontSize: "14px", fontWeight: 600 }}>
        No privacy notices found.
      </span>
      <span style={{ fontSize: "12px" }}>
        Click &quot;Add a privacy notice&quot; to add your first privacy notice
        to Fides.
      </span>
    </VStack>
    <NextLink href={`${PRIVACY_NOTICES_ROUTE}/new`} passHref legacyBehavior>
      <Button type="primary" size="small" data-testid="add-privacy-notice-btn">
        Add a privacy notice +
      </Button>
    </NextLink>
  </VStack>
);

// Cell component for consent mechanism
const MechanismCellRenderer = ({ value }: { value: ConsentMechanism }) => {
  const innerText = MECHANISM_MAP.get(value!) ?? value;
  return (
    <Tag data-testid="mechanism-badge" style={{ textTransform: "uppercase" }}>
      {innerText}
    </Tag>
  );
};

// Cell component for privacy notice status
type TagNames = "available" | "enabled" | "inactive";

const systemsApplicableTags: Record<
  TagNames,
  { color: CUSTOM_TAG_COLOR; tooltip: string }
> = {
  available: {
    color: CUSTOM_TAG_COLOR.WARNING,
    tooltip:
      "This notice is associated with a system + data use and can be enabled",
  },
  enabled: {
    color: CUSTOM_TAG_COLOR.SUCCESS,
    tooltip: "This notice is active and available for consumers",
  },
  inactive: {
    color: CUSTOM_TAG_COLOR.DEFAULT,
    tooltip:
      "This privacy notice cannot be enabled because it either does not have a data use or the linked data use has not been assigned to a system",
  },
};

const StatusCellRenderer = ({
  record,
}: {
  record: LimitedPrivacyNoticeResponseSchema;
}) => {
  let tagValue: TagNames | undefined;
  const {
    systems_applicable: systemsApplicable,
    disabled,
    data_uses: dataUses,
  } = record;
  if (!dataUses) {
    tagValue = "inactive";
  } else if (systemsApplicable) {
    tagValue = disabled ? "available" : "enabled";
  } else {
    tagValue = "inactive";
  }
  const { tooltip = undefined, ...tagProps } = tagValue
    ? systemsApplicableTags[tagValue]
    : { color: CUSTOM_TAG_COLOR.DEFAULT };

  return (
    <Tooltip title={tooltip}>
      <span>
        <Tag
          color={tagProps.color}
          data-testid="status-badge"
          style={{ textTransform: "uppercase" }}
        >
          {tagValue}
        </Tag>
      </span>
    </Tooltip>
  );
};

// Cell component for enable toggle
const EnablePrivacyNoticeCellRenderer = ({
  record,
}: {
  record: LimitedPrivacyNoticeResponseSchema;
}) => {
  const [patchNoticeMutationTrigger] = useLimitedPatchPrivacyNoticesMutation();
  const [isLoading, setIsLoading] = useState(false);

  const onToggle = async (toggle: boolean) => {
    setIsLoading(true);
    const response = await patchNoticeMutationTrigger({
      id: record.id,
      disabled: !toggle,
    });
    setIsLoading(false);
    return response;
  };

  const {
    systems_applicable: systemsApplicable,
    disabled: noticeIsDisabled,
    data_uses: dataUses,
  } = record;
  const hasDataUses = !!dataUses;
  const toggleIsDisabled =
    (noticeIsDisabled && !systemsApplicable) || !hasDataUses;

  return (
    <EnableCell
      enabled={!record.disabled}
      isDisabled={toggleIsDisabled}
      onToggle={onToggle}
      title="Disable privacy notice"
      message="Are you sure you want to disable this privacy notice? Disabling this
        notice means your users will no longer see this explanation about
        your data uses which is necessary to ensure compliance."
      loading={isLoading}
    />
  );
};

// Cell component for children count
const ChildrenCellRenderer = ({
  noticeChildren,
}: {
  noticeChildren: LimitedPrivacyNoticeResponseSchema["children"];
}) => {
  const childrenCount = noticeChildren?.length ?? 0;
  if (childrenCount === 0) {
    return <span>Unassigned</span>;
  }
  return (
    <Tag data-testid="children-badge">
      {childrenCount} {childrenCount === 1 ? "Child" : "Children"}
    </Tag>
  );
};

const usePrivacyNoticesTable = () => {
  const router = useRouter();

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_NOTICE_UPDATE,
  ]);

  // Table state management
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

  // Row click handler
  const onRowClick = (record: LimitedPrivacyNoticeResponseSchema) => {
    if (userCanUpdate) {
      router.push(`${PRIVACY_NOTICES_ROUTE}/${record.id}`);
    }
  };

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
          render: (
            value: LimitedPrivacyNoticeResponseSchema["consent_mechanism"],
          ) => <MechanismCellRenderer value={value} />,
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
            <StatusCellRenderer record={record} />
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
          render: (
            noticeChildren: LimitedPrivacyNoticeResponseSchema["children"],
          ) => <ChildrenCellRenderer noticeChildren={noticeChildren} />,
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
                ) => <EnablePrivacyNoticeCellRenderer record={record} />,
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
    onRowClick,
    isEmpty: !isLoading && items.length === 0,
  };
};

export const PrivacyNoticesTableV2 = () => {
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();

  const { tableProps, columns, userCanUpdate, onRowClick, isEmpty } =
    usePrivacyNoticesTable();

  if (isLoadingHealthCheck) {
    return (
      <Flex justify="center" align="center" style={{ padding: "40px" }}>
        <span>Loading...</span>
      </Flex>
    );
  }

  return (
    <Flex vertical gap="middle" style={{ width: "100%" }}>
      {userCanUpdate && (
        <Flex justify="flex-end">
          <NextLink
            href={`${PRIVACY_NOTICES_ROUTE}/new`}
            passHref
            legacyBehavior
          >
            <Button type="primary" data-testid="add-privacy-notice-btn">
              Add a privacy notice +
            </Button>
          </NextLink>
        </Flex>
      )}
      {isEmpty ? (
        <EmptyTableNotice />
      ) : (
        <Table
          {...tableProps}
          columns={columns}
          onRow={(record) => ({
            onClick: () => onRowClick(record),
            style: userCanUpdate ? { cursor: "pointer" } : undefined,
          })}
        />
      )}
    </Flex>
  );
};
