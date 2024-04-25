// /* eslint-disable react/no-unstable-nested-components */

// import { Text, VStack } from "@fidesui/react";
// import {
//   ColumnDef,
//   getCoreRowModel,
//   getExpandedRowModel,
//   getGroupedRowModel,
//   useReactTable,
// } from "@tanstack/react-table";
// import { useEffect, useMemo } from "react";

// import {
//   FidesTableV2,
//   PaginationBar,
//   TableSkeletonLoader,
//   useServerSidePagination,
// } from "~/features/common/table/v2";
// import { useGetMonitorResultsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
// import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
// import useStagedResourceColumns from "~/features/data-discovery-and-detection/hooks/useStagedResourceColumns";
// import { StagedResource } from "~/types/api";

// const EMPTY_RESPONSE = {
//   items: [],
//   total: 0,
//   page: 1,
//   size: 50,
//   pages: 1,
// };

// const EmptyTableNotice = () => (
//   <VStack
//     mt={6}
//     p={10}
//     spacing={4}
//     borderRadius="base"
//     maxW="70%"
//     data-testid="empty-state"
//     alignSelf="center"
//     margin="auto"
//   >
//     <VStack>
//       <Text fontSize="md" fontWeight="600">
//         No results found.
//       </Text>
//       <Text fontSize="sm">
//         [insert some copy about how to find results here]
//       </Text>
//     </VStack>
//   </VStack>
// );

// interface MonitorResultTableProps {
//   resourceUrn?: string;
// }

// const DiscoveryMonitorResultTable = ({
//   resourceUrn,
// }: MonitorResultTableProps) => {
//   const {
//     PAGE_SIZES,
//     pageSize,
//     setPageSize,
//     onPreviousPageClick,
//     isPreviousPageDisabled,
//     onNextPageClick,
//     isNextPageDisabled,
//     startRange,
//     endRange,
//     pageIndex,
//     setTotalPages,
//   } = useServerSidePagination();

//   const {
//     isFetching,
//     isLoading,
//     data: resources,
//   } = useGetMonitorResultsQuery({
//     staged_resource_urn: resourceUrn,
//     page: pageIndex,
//     size: pageSize,
//   });

//   const resourceType = findResourceType(
//     resources?.items[0] as DiscoveryMonitorItem
//   );

//   const { columns } = useStagedResourceColumns({ resourceType });

//   const {
//     items: data,
//     total: totalRows,
//     pages: totalPages,
//   } = useMemo(() => resources ?? EMPTY_RESPONSE, [resources]);

//   useEffect(() => {
//     setTotalPages(totalPages);
//   }, [totalPages, setTotalPages]);

//   const resourceColumns: ColumnDef<StagedResource, any>[] = useMemo(
//     () => columns,
//     [columns]
//   );

//   const { navigateToResourceResults } = useDiscoveryRoutes();

//   const handleRowClicked =
//     resourceType !== StagedResourceType.FIELD
//       ? (row: StagedResource) => navigateToResourceResults(row)
//       : undefined;

//   const tableInstance = useReactTable<StagedResource>({
//     getCoreRowModel: getCoreRowModel(),
//     getGroupedRowModel: getGroupedRowModel(),
//     getExpandedRowModel: getExpandedRowModel(),
//     columns: resourceColumns,
//     manualPagination: true,
//     data,
//   });

//   if (isLoading) {
//     return <TableSkeletonLoader rowHeight={36} numRows={36} />;
//   }

//   return (
//     <>
//       <FidesTableV2
//         tableInstance={tableInstance}
//         onRowClick={handleRowClicked}
//         emptyTableNotice={<EmptyTableNotice />}
//       />
//       <PaginationBar
//         totalRows={totalRows}
//         pageSizes={PAGE_SIZES}
//         setPageSize={setPageSize}
//         onPreviousPageClick={onPreviousPageClick}
//         isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
//         onNextPageClick={onNextPageClick}
//         isNextPageDisabled={isNextPageDisabled || isFetching}
//         startRange={startRange}
//         endRange={endRange}
//       />
//     </>
//   );
// };

// export default DiscoveryMonitorResultTable;
