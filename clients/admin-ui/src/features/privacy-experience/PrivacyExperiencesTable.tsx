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
  CustomAssetType,
  ExperienceConfigListViewResponse,
  ScopeRegistryEnum,
} from "~/types/api";

import { PRIVACY_EXPERIENCE_ROUTE } from "../common/nav/v2/routes";
import Restrict, { useHasPermission } from "../common/Restrict";
import CustomAssetUploadButton from "../custom-assets/CustomAssetUploadButton";
import { getRegions } from "../privacy-notices/cells";
import { ComponentCell, EnablePrivacyExperienceCell } from "./cells";
import JavaScriptTag from "./JavaScriptTag";
import { useGetAllExperienceConfigsQuery } from "./privacy-experience.slice";

const emptyExperienceResponse = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const EmptyTableExperience = () => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="empty-state"
    alignSelf="center"
    margin="auto"
  >
    <VStack>
      <Text fontSize="md" fontWeight="600">
        No privacy experiences found.
      </Text>
      <Text fontSize="sm">
        Click &quot;Create new experience&quot; to add your first privacy
        experience to Fides.
      </Text>
    </VStack>
    <NextLink href={`${PRIVACY_EXPERIENCE_ROUTE}/new`}>
      <Button
        size="xs"
        colorScheme="primary"
        data-testid="add-privacy-experience-btn"
      >
        Create new experience
      </Button>
    </NextLink>
  </VStack>
);
const columnHelper = createColumnHelper<ExperienceConfigListViewResponse>();

export const PrivacyExperiencesTable = () => {
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
  const router = useRouter();

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_EXPERIENCE_UPDATE,
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
    data: experiences,
  } = useGetAllExperienceConfigsQuery({
    page: pageIndex,
    size: pageSize,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => experiences || emptyExperienceResponse, [experiences]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const inventoryColumns: ColumnDef<ExperienceConfigListViewResponse, any>[] =
    useMemo(
      () =>
        [
          columnHelper.accessor((row) => row.name, {
            id: "name",
            cell: (props) => <DefaultCell value={props.getValue()} />,
            header: (props) => <DefaultHeaderCell value="Title" {...props} />,
          }),
          columnHelper.accessor((row) => row.component, {
            id: "component",
            cell: (props) => ComponentCell(props.getValue()),
            header: (props) => (
              <DefaultHeaderCell value="Component" {...props} />
            ),
          }),
          columnHelper.accessor((row) => row.regions, {
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
          columnHelper.accessor((row) => row.updated_at, {
            id: "updated_at",
            cell: (props) => (
              <DefaultCell value={new Date(props.getValue()).toDateString()} />
            ),
            header: (props) => (
              <DefaultHeaderCell value="Last update" {...props} />
            ),
          }),
          userCanUpdate &&
            columnHelper.accessor((row) => row.disabled, {
              id: "enable",
              cell: (props) => EnablePrivacyExperienceCell(props),
              header: (props) => (
                <DefaultHeaderCell value="Enable" {...props} />
              ),
            }),
        ].filter(Boolean) as ColumnDef<ExperienceConfigListViewResponse, any>[],
      [userCanUpdate]
    );

  const tableInstance = useReactTable<ExperienceConfigListViewResponse>({
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

  const onRowClick = ({ id }: ExperienceConfigListViewResponse) => {
    if (userCanUpdate) {
      router.push(`${PRIVACY_EXPERIENCE_ROUTE}/${id}`);
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
            <HStack alignItems="center" spacing={4}>
              <JavaScriptTag />
              <Restrict scopes={[ScopeRegistryEnum.CUSTOM_ASSET_UPDATE]}>
                <CustomAssetUploadButton
                  assetType={CustomAssetType.CUSTOM_FIDES_CSS}
                />
              </Restrict>
            </HStack>
            <NextLink href={`${PRIVACY_EXPERIENCE_ROUTE}/new`}>
              <Button
                size="xs"
                colorScheme="primary"
                data-testid="add-privacy-ecperience-btn"
              >
                Create new experience
              </Button>
            </NextLink>
          </TableActionBar>
        )}
        <FidesTableV2
          tableInstance={tableInstance}
          onRowClick={userCanUpdate ? onRowClick : undefined}
          emptyTableNotice={<EmptyTableExperience />}
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
