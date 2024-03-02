/* eslint-disable react/no-unstable-nested-components */
import { Button, Flex, HStack, Text, VStack } from "@fidesui/react";
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
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useEffect, useMemo } from "react";

import { useGetHealthQuery } from "~/features/plus/plus.slice";
import {
  EnablePrivacyNoticeCell,
  getRegions,
  MechanismCell,
  PrivacyNoticeStatusCell,
} from "~/features/privacy-notices/cells";
import { useGetAllPrivacyNoticesQuery } from "~/features/privacy-notices/privacy-notices.slice";
import {
  LimitedPrivacyNoticeResponseSchema,
  ScopeRegistryEnum,
} from "~/types/api";

import { PRIVACY_NOTICES_ROUTE } from "../common/nav/v2/routes";
import { useHasPermission } from "../common/Restrict";
import { FRAMEWORK_MAP } from "./constants";

const emptyNoticeResponse = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

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
      <Text fontSize="md" fontWeight="600">
        No privacy notices found.
      </Text>
      <Text fontSize="sm">
        Click &quot;Add a privacy notice&quot; to add your first privacy notice
        to Fides.
      </Text>
    </VStack>
    <NextLink href={`${PRIVACY_NOTICES_ROUTE}/new`}>
      <Button
        size="xs"
        colorScheme="primary"
        data-testid="add-privacy-notice-btn"
      >
        Add a privacy notice +
      </Button>
    </NextLink>
  </VStack>
);
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

  const inventoryColumns: ColumnDef<LimitedPrivacyNoticeResponseSchema, any>[] =
    useMemo(
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
            header: (props) => (
              <DefaultHeaderCell value="Mechanism" {...props} />
            ),
          }),
          columnHelper.accessor((row) => row.configured_regions, {
            id: "regions",
            cell: (props) => (
              <GroupCountBadgeCell
                suffix="Locations"
                value={getRegions(props.getValue())}
                {...props}
              />
            ),
            header: (props) => (
              <DefaultHeaderCell value="Locations" {...props} />
            ),
            meta: {
              displayText: "Locations",
              showHeaderMenu: true,
            },
          }),
          // columnHelper.accessor((row) => row.updated_at, {
          //   id: "updated_at",
          //   cell: (props) => (
          //     <DefaultCell value={new Date(props.getValue()).toDateString()} />
          //   ),
          //   header: (props) => (
          //     <DefaultHeaderCell value="Last update" {...props} />
          //   ),
          // }),
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
            header: (props) => (
              <DefaultHeaderCell value="Farmework" {...props} />
            ),
          }),
          userCanUpdate &&
            columnHelper.accessor((row) => row.disabled, {
              id: "enable",
              cell: (props) => EnablePrivacyNoticeCell(props),
              header: (props) => (
                <DefaultHeaderCell value="Enable" {...props} />
              ),
            }),
        ].filter(Boolean) as ColumnDef<
          LimitedPrivacyNoticeResponseSchema,
          any
        >[],
      [userCanUpdate]
    );

  const tableInstance = useReactTable<LimitedPrivacyNoticeResponseSchema>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: inventoryColumns,
    manualPagination: true,
    data,
    state: {
      expanded: true,
    },
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
              <NextLink href={`${PRIVACY_NOTICES_ROUTE}/new`}>
                <Button
                  size="xs"
                  colorScheme="primary"
                  data-testid="add-privacy-notice-btn"
                >
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
          totalRows={totalRows}
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
