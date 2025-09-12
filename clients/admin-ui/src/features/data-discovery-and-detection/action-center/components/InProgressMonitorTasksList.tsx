import {
  AntFlex as Flex,
  AntList as List,
} from "fidesui";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import { MonitorTaskInProgressResponse } from "~/types/api";

import { useInProgressMonitorTasksList } from "../hooks/useInProgressMonitorTasksList";
import { useShowCompletedState } from "../hooks/useShowCompletedState";
import { InProgressMonitorTaskItem } from "./InProgressMonitorTaskItem";

interface InProgressMonitorTasksListProps {
  monitorId?: string;
}

export const InProgressMonitorTasksList = ({
  monitorId,
}: InProgressMonitorTasksListProps) => {
  const { showCompleted } = useShowCompletedState();

  const {
    // List state and data
    searchQuery,
    updateSearch,

    // Ant Design list integration
    listProps,

    // Loading states
    isLoading,
    isFetching,
  } = useInProgressMonitorTasksList({ monitorId, showCompleted });

  return (
    <>
      <Flex justify="space-between" align="center" className="mb-4">
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          placeholder="Search by monitor name..."
        />
      </Flex>

      <List
        {...listProps}
        renderItem={(task: MonitorTaskInProgressResponse) => (
          <List.Item>
            <InProgressMonitorTaskItem task={task} />
          </List.Item>
        )}
      />
    </>
  );
};
