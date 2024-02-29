/* eslint-disable react/no-unstable-nested-components */
import { Button, Flex, HStack, Text, VStack } from "@fidesui/react";
import {
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
    GlobalFilterV2,
    GroupCountBadgeCell,
    PaginationBar,
    TableActionBar,
    TableSkeletonLoader,
    useServerSidePagination,
} from "common/table/v2";
import {
    EnablePrivacyNoticeCell,
    getRegions,
    MechanismCell,
    PrivacyNoticeStatusCell,
} from "~/features/privacy-notices/cells";
import _ from "lodash";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";

import NextLink from "next/link";

import { useGetHealthQuery } from "~/features/plus/plus.slice";
import { useGetAllPrivacyNoticesQuery } from "~/features/privacy-notices/privacy-notices.slice";
import { PrivacyNoticeRegion, PrivacyNoticeResponse, ScopeRegistryEnum } from "~/types/api";
import { PRIVACY_NOTICES_ROUTE } from "../common/nav/v2/routes";
import { PRIVACY_NOTICE_REGION_MAP } from "../common/privacy-notice-regions";
import { FRAMEWORK_MAP } from "./constants";
import { useHasPermission } from "../common/Restrict";

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
                Click “Add a privacy notice" to add your first privacy notice to Fides.
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
const columnHelper = createColumnHelper<PrivacyNoticeResponse>();

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
        resetPageIndexToDefault,
    } = useServerSidePagination();

    const [globalFilter, setGlobalFilter] = useState<string>();

    const updateGlobalFilter = (searchTerm: string) => {
        resetPageIndexToDefault();
        setGlobalFilter(searchTerm);
    };

    const {
        isFetching,
        isLoading,
        data: notices,
    } = useGetAllPrivacyNoticesQuery({
        page: pageIndex,
        size: pageSize,
        // search: globalFilter,
    });

    const {
        items: data,
        total: totalRows,
        pages: totalPages,
    } = useMemo(() => notices || emptyNoticeResponse, [notices]);

    useEffect(() => {
        setTotalPages(totalPages);
    }, [totalPages, setTotalPages]);

    const inventoryColumns = useMemo(
        () => [
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
            columnHelper.accessor((row) => row.regions, {
                id: "regions",
                cell: (props) => (

                    <GroupCountBadgeCell
                        suffix="Locations"
                        value={getRegions(props.getValue())}
                        {...props}
                    />
                ),
                header: (props) => <DefaultHeaderCell value="Locations" {...props} />,
                meta: {
                    displayText: "Locations",
                    showHeaderMenu: true,
                },
            }),
            columnHelper.accessor((row) => row.updated_at, {
                id: "updated_at",
                cell: (props) => <DefaultCell value={new Date(props.getValue()).toDateString()} />,
                header: (props) => <DefaultHeaderCell value="Last update" {...props} />,
            }),
            columnHelper.accessor((row) => row.disabled, {
                id: "status",
                cell: (props) => PrivacyNoticeStatusCell(props),
                header: (props) => <DefaultHeaderCell value="Status" {...props} />,
            }),
            columnHelper.accessor((row) => row.framework, {
                id: "framework",
                cell: (props) => (props.getValue() ? <BadgeCell value={FRAMEWORK_MAP.get(props.getValue()!)!} /> : null),
                header: (props) => <DefaultHeaderCell value="Farmework" {...props} />,
            }),
            columnHelper.accessor((row) => row.disabled, {
                id: "enable",
                cell: (props) => EnablePrivacyNoticeCell(props),
                header: (props) => <DefaultHeaderCell value="Enable" {...props} />,
            }),
        ],
        []
    );

    const tableInstance = useReactTable<PrivacyNoticeResponse>({
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

    const onRowClick = ({ id }: PrivacyNoticeResponse) => {
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
                <TableActionBar>
                    <GlobalFilterV2
                        globalFilter={globalFilter}
                        setGlobalFilter={updateGlobalFilter}
                        placeholder="Search property"
                    />
                    <HStack alignItems="center" spacing={4}>
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
