/* eslint-disable react/no-unstable-nested-components */
import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GroupCountBadgeCell,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "common/table/v2";
import { AntButton as Button, Flex, HStack, Text, VStack } from "fidesui";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useEffect, useMemo } from "react";

import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { useHasPermission } from "~/features/common/Restrict";
import { BadgeCellExpandable } from "~/features/common/table/v2/cells";
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import {
  EnablePrivacyNoticeCell,
  getNoticeChildren,
  MechanismCell,
  PrivacyNoticeStatusCell,
} from "~/features/privacy-notices/cells";
import { FRAMEWORK_MAP } from "~/features/privacy-notices/constants";
import { useGetAllPrivacyNoticesQuery } from "~/features/privacy-notices/privacy-notices.slice";
import {
  LimitedPrivacyNoticeResponseSchema,
  PrivacyNoticeRegion,
  ScopeRegistryEnum,
} from "~/types/api";

const emptyNoticeResponse = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const EmptyTableNotice = () => {
  return (
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
        <Text fontSize="md" fontWeight="600">
          No privacy notices found.
        </Text>
        <Text fontSize="sm">
          Click &quot;Add a privacy notice&quot; to add your first privacy
          notice to Fides.
        </Text>
      </VStack>
      <Button
        href={`${PRIVACY_NOTICES_ROUTE}/new`}
        role="link"
        size="small"
        type="primary"
        data-testid="add-privacy-notice-btn"
      >
        Add a privacy notice +
      </Button>
    </VStack>
  );
};
const columnHelper = createColumnHelper<LimitedPrivacyNoticeResponseSchema>();

export const PrivacyNoticesTable = () => {
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
  const router = useRouter();

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_NOTICE_UPDATE,
  ]);

  const {
    PAGE_SIZES,
    pageSize,
    setPageSize,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    startRange,
    endRange,
    pageIndex,
    setTotalPages,
  } = useServerSidePagination();

  const {
    isFetching,
    isLoading,
    data: notices,
  } = useGetAllPrivacyNoticesQuery({
    page: pageIndex,
    size: pageSize,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => notices || emptyNoticeResponse, [notices]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const privacyNoticeColumns: ColumnDef<
    LimitedPrivacyNoticeResponseSchema,
    any
  >[] = useMemo(
    () =>
      [
        columnHelper.accessor((row) => row.name, {
          id: "name",
          cell: (props) => <DefaultCell value={props.getValue()} />,
          header: (props) => <DefaultHeaderCell value="Title" {...props} />,
        }),
        columnHelper.accessor((row) => row.consent_mechanism, {
          id: "consent_mechanism",
          cell: (props) => MechanismCell(props.getValue()),
          header: (props) => <DefaultHeaderCell value="Mechanism" {...props} />,
        }),
        columnHelper.accessor((row) => row.configured_regions, {
          id: "regions",
          cell: (props) => (
            <BadgeCellExpandable
              values={
                props.getValue()?.map((location: PrivacyNoticeRegion) => ({
                  label: PRIVACY_NOTICE_REGION_RECORD[location] ?? location,
                  key: location,
                })) ?? []
              }
              cellProps={props}
            />
          ),
          header: (props) => <DefaultHeaderCell value="Locations" {...props} />,
          size: 250,
          meta: {
            showHeaderMenu: true,
            disableRowClick: true,
          },
        }),
        columnHelper.accessor((row) => row.disabled, {
          id: "status",
          cell: (props) => PrivacyNoticeStatusCell(props),
          header: (props) => <DefaultHeaderCell value="Status" {...props} />,
        }),
        columnHelper.accessor((row) => row.framework, {
          id: "framework",
          cell: (props) =>
            props.getValue() ? (
              <BadgeCell value={FRAMEWORK_MAP.get(props.getValue()!)!} />
            ) : null,
          header: (props) => <DefaultHeaderCell value="Framework" {...props} />,
        }),
        columnHelper.accessor((row) => row.children, {
          id: "children",
          cell: (props) =>
            getNoticeChildren(props.getValue())?.length ? (
              <GroupCountBadgeCell
                suffix="Children"
                value={getNoticeChildren(props.getValue())}
                {...props}
              />
            ) : (
              <DefaultCell value="Unassigned" />
            ),
          header: (props) => <DefaultHeaderCell value="Children" {...props} />,
          meta: {
            showHeaderMenu: true,
          },
        }),
        userCanUpdate &&
          columnHelper.accessor((row) => row.disabled, {
            id: "enable",
            cell: EnablePrivacyNoticeCell,
            header: (props) => <DefaultHeaderCell value="Enable" {...props} />,
            meta: { disableRowClick: true },
          }),
      ].filter(Boolean) as ColumnDef<LimitedPrivacyNoticeResponseSchema, any>[],
    [userCanUpdate],
  );

  const tableInstance = useReactTable<LimitedPrivacyNoticeResponseSchema>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: privacyNoticeColumns,
    manualPagination: true,
    data,
    state: {
      expanded: true,
    },
    columnResizeMode: "onChange",
  });

  const onRowClick = ({ id }: LimitedPrivacyNoticeResponseSchema) => {
    if (userCanUpdate) {
      router.push(`${PRIVACY_NOTICES_ROUTE}/${id}`);
    }
  };

  if (isLoading || isLoadingHealthCheck) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }
  return (
    <div>
      <Flex flex={1} direction="column" overflow="auto">
        {userCanUpdate && (
          <TableActionBar>
            <HStack alignItems="center" spacing={4} marginLeft="auto">
              <NextLink
                href={`${PRIVACY_NOTICES_ROUTE}/new`}
                passHref
                legacyBehavior
              >
                <Button type="primary" data-testid="add-privacy-notice-btn">
                  Add a privacy notice +
                </Button>
              </NextLink>
            </HStack>
          </TableActionBar>
        )}
        <FidesTableV2
          tableInstance={tableInstance}
          onRowClick={userCanUpdate ? onRowClick : undefined}
          emptyTableNotice={<EmptyTableNotice />}
        />
        <PaginationBar
          totalRows={totalRows || 0}
          pageSizes={PAGE_SIZES}
          setPageSize={setPageSize}
          onPreviousPageClick={onPreviousPageClick}
          isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
          onNextPageClick={onNextPageClick}
          isNextPageDisabled={isNextPageDisabled || isFetching}
          startRange={startRange}
          endRange={endRange}
        />
      </Flex>
    </div>
  );
};
