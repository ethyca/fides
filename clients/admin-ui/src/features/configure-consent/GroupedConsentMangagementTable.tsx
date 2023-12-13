/* eslint-disable react/no-unstable-nested-components */
import {
  Button,
  Flex,
  ChevronDownIcon,
  Menu,
  MenuButton,
  MenuList,
  MenuItemOption,
  Portal,
} from "@fidesui/react";
import {
  createColumnHelper,
  getCoreRowModel,
  getPaginationRowModel,
  getGroupedRowModel,
  getExpandedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useFeatures } from "common/features";
import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  GroupCountBadgeCell,
  useServerSidePagination,
} from "common/table/v2";
import { useEffect, useMemo, useState } from "react";

import {
  ConsentManagementFilterModal,
  Option,
  useConsentManagementFilters,
} from "~/features/configure-consent/ConsentManagementFilterModal";
import {
  ConsentManagementModal,
  useConsentManagementModal,
} from "~/features/configure-consent/ConsentManagementModal";
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import { DATAMAP_GROUPING } from "~/types/api";
import {
  useGetMininimalDatamapReportQuery,
  Page_MinimalDatamapGrouping,
  MinimalDatamapGrouping,
} from "~/features/datamap/datamap.slice";

const columnHelper = createColumnHelper<MinimalDatamapGrouping>();

const emptyMinimalDatamapReportResponse: Page_MinimalDatamapGrouping = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};
export const GroupedConsentManagementTable = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
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
    resetPageIndexToDefault,
  } = useServerSidePagination();
  const [groupBy, setGroupBy] = useState<DATAMAP_GROUPING>(
    DATAMAP_GROUPING.SYSTEM_DATA_USE
  );

  const {
    data: datamapReport,
    isLoading: isReportLoading,
    isFetching: isReportFetching,
  } = useGetMininimalDatamapReportQuery({
    organizationName: "default_organization",
    pageIndex,
    pageSize,
    groupBy,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(
    () => datamapReport || emptyMinimalDatamapReportResponse,
    [datamapReport]
  );

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const tcfColumns = useMemo(
    () => [
      columnHelper.accessor((row) => row.system_name, {
        enableGrouping: true,
        id: "system_name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Vendor" {...props} />,
        meta: {
          maxWidth: "350px",
        },
      }),
      columnHelper.accessor((row) => row.data_use, {
        id: "data_use",
        cell: (props) => <BadgeCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Data use" {...props} />,
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.data_categories, {
        id: "data_categories",
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data categories"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data categories" {...props} />
        ),
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.data_subjects, {
        id: "data_subjects",
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data subjects"
            expand={true}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data subject" {...props} />
        ),
        meta: {
          width: "175px",
        },
      }),
    ],
    []
  );
  const grouping = useMemo(() => {
    switch (groupBy) {
      case DATAMAP_GROUPING.SYSTEM_DATA_USE: {
        return ["system_name"];
      }
      case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
        return ["data_use"];
      }
    }
  }, [groupBy]);

  const tableInstance = useReactTable<MinimalDatamapGrouping>({
    columns: tcfColumns,
    getGroupedRowModel: getGroupedRowModel(),
    manualPagination: true,
    getExpandedRowModel: getExpandedRowModel(),
    data,
    debugTable: true,
    state: {
      expanded: true,
      grouping,
    },
    getCoreRowModel: getCoreRowModel(),
  });

  const getMenuDisplayValue = () => {
    switch (groupBy) {
      case DATAMAP_GROUPING.SYSTEM_DATA_USE: {
        return "system";
      }
      case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
        return "data use";
      }
    }
  };

  if (isReportLoading || isLoadingHealthCheck) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }

  return (
    <Flex flex={1} direction="column" overflow="auto">
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={""}
          setGlobalFilter={() => {}}
          placeholder="Search"
        />
        <Flex alignItems="center">
          <Menu>
            <MenuButton
              as={Button}
              size="xs"
              variant="outline"
              mr={2}
              rightIcon={<ChevronDownIcon />}
            >
              Group by {getMenuDisplayValue()}
            </MenuButton>
            <MenuList zIndex={11}>
              <MenuItemOption
                onClick={() => {
                  setGroupBy(DATAMAP_GROUPING.SYSTEM_DATA_USE);
                }}
                isChecked={DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy}
                value={DATAMAP_GROUPING.SYSTEM_DATA_USE}
              >
                System
              </MenuItemOption>
              <MenuItemOption
                onClick={() => {
                  setGroupBy(DATAMAP_GROUPING.DATA_USE_SYSTEM);
                }}
                isChecked={DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy}
                value={DATAMAP_GROUPING.DATA_USE_SYSTEM}
              >
                Data use
              </MenuItemOption>
              <MenuItemOption value={DATAMAP_GROUPING.SYSTEM_DATA_USE}>
                Data category
              </MenuItemOption>
            </MenuList>
          </Menu>
          <Button
            data-testid="filter-multiple-systems-btn"
            size="xs"
            variant="outline"
          >
            Filter
          </Button>
        </Flex>
      </TableActionBar>

      <FidesTableV2<MinimalDatamapGrouping> tableInstance={tableInstance} />
      <PaginationBar
        totalRows={totalRows}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isReportFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isReportFetching}
        startRange={startRange}
        endRange={endRange}
      />
    </Flex>
  );
};
