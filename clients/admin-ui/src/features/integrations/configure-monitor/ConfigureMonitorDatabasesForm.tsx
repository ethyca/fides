import { Button, ButtonGroup, Flex, Spinner, Text } from "fidesui";
import { useEffect, useState } from "react";

import useQueryResultToast from "~/features/common/form/useQueryResultToast";
import { PickerCheckboxList } from "~/features/common/PickerCard";
import {
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import {
  useGetDatabasesByMonitorQuery,
  usePutDiscoveryMonitorMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { MonitorConfig } from "~/types/api";
import { isErrorResult } from "~/types/errors";

const EMPTY_RESPONSE = {
  items: [] as string[],
  total: 0,
  page: 1,
  size: 50,
  pages: 0,
};

const ConfigureMonitorDatabasesForm = ({
  monitor,
  onClose,
}: {
  monitor: MonitorConfig;
  onClose: () => void;
}) => {
  const { toastResult } = useQueryResultToast({
    defaultSuccessMsg: "Monitor updated successfully",
    defaultErrorMsg: "A problem occurred while updating this monitor",
  });

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

  const { data, isLoading, isFetching } = useGetDatabasesByMonitorQuery({
    page: pageIndex,
    size: pageSize,
    monitor_config_id: monitor.key!,
  });
  const {
    items: databases,
    total: totalRows,
    pages: totalPages,
  } = data ?? EMPTY_RESPONSE;

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const [putMonitorMutationTrigger] = usePutDiscoveryMonitorMutation();

  const [selected, setSelected] = useState<string[]>(monitor.databases ?? []);

  const handleSave = async () => {
    const payload = { ...monitor, databases: selected };
    const result = await putMonitorMutationTrigger(payload);
    toastResult(result);
    if (!isErrorResult(result)) {
      onClose();
    }
  };

  if (isLoading) {
    return (
      <Flex align="center" justify="center">
        <Spinner />
      </Flex>
    );
  }

  return (
    <>
      <Flex p={4} direction="column">
        <Text mb={4} fontSize="sm">
          Select projects to restrict which datasets this monitor can access. If
          no projects are selected, the monitor will observe all current and
          future projects.
        </Text>
        <PickerCheckboxList
          title="Select all projects"
          items={databases.map((d) => ({ id: d, name: d }))}
          selected={selected}
          onChange={setSelected}
          numSelected={selected.length}
          indeterminate={[]}
        />
      </Flex>
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
      <ButtonGroup size="sm" w="full" justifyContent="space-between" mt={4}>
        <Button onClick={onClose} variant="outline">
          Cancel
        </Button>
        <Button onClick={handleSave} variant="primary" data-testid="save-btn">
          Save
        </Button>
      </ButtonGroup>
    </>
  );
};

export default ConfigureMonitorDatabasesForm;
