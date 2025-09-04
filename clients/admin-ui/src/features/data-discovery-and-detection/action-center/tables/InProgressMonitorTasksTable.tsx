import {
  AntFlex as Flex,
  AntTable as Table,
} from "fidesui";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import { useInProgressMonitorTasksColumns } from "../hooks/useInProgressMonitorTasksColumns";
import { useInProgressMonitorTasksTable } from "../hooks/useInProgressMonitorTasksTable";

interface InProgressMonitorTasksTableProps {
  monitorId?: string;
}

export const InProgressMonitorTasksTable = ({
  monitorId,
}: InProgressMonitorTasksTableProps) => {
  const {
    // Table state and data
    searchQuery,
    updateSearch,

    // Ant Design table integration
    tableProps,

    // Loading states
    isLoading,
    isFetching,
  } = useInProgressMonitorTasksTable({ monitorId });

  const { columns } = useInProgressMonitorTasksColumns();

  return (
    <>
      <Flex justify="space-between" align="center" className="mb-4">
        <DebouncedSearchInput 
          value={searchQuery} 
          onChange={updateSearch}
          placeholder="Search by monitor name..."
        />
      </Flex>
      <Table 
        {...tableProps} 
        columns={columns}
        loading={isLoading || isFetching}
      />
    </>
  );
};
