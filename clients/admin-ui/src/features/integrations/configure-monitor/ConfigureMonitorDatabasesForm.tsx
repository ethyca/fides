import { Button, ButtonGroup, Flex, Text, Tooltip } from "fidesui";
import { useEffect, useState } from "react";

import FidesSpinner from "~/features/common/FidesSpinner";
import useQueryResultToast from "~/features/common/form/useQueryResultToast";
import { usePaginatedPicker } from "~/features/common/hooks/usePicker";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import {
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import {
  useGetDatabasesByConnectionQuery,
  usePutDiscoveryMonitorMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import MonitorDatabasePicker from "~/features/integrations/configure-monitor/MonitorDatabasePicker";
import { MonitorConfig } from "~/types/api";
import { isErrorResult } from "~/types/errors";

const EMPTY_RESPONSE = {
  items: [] as string[],
  total: 0,
  page: 1,
  size: 50,
  pages: 0,
};

const TOOLTIP_COPY =
  "Select projects to restrict which datasets this monitor can access. If no projects are selected, the monitor will observe all current and future projects.";

const ConfigureMonitorDatabasesForm = ({
  monitor,
  isEditing,
  integrationKey,
  onClose,
}: {
  monitor: MonitorConfig;
  isEditing?: boolean;
  integrationKey: string;
  onClose: () => void;
}) => {
  const { toastResult } = useQueryResultToast({
    defaultSuccessMsg: `Monitor ${
      isEditing ? "updated" : "created"
    } successfully`,
    defaultErrorMsg: `A problem occurred while ${
      isEditing ? "updating" : "creating"
    } this monitor`,
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

  const { data, isLoading, isFetching } = useGetDatabasesByConnectionQuery({
    page: pageIndex,
    size: pageSize,
    connection_config_key: integrationKey,
  });

  const {
    items: databases,
    total: totalRows,
    pages: totalPages,
  } = data ?? EMPTY_RESPONSE;

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const [putMonitorMutationTrigger, { isLoading: isSubmitting }] =
    usePutDiscoveryMonitorMutation();

  const [selected, setSelected] = useState<string[]>(monitor.databases ?? []);

  const { allSelected, someSelected, handleToggleSelection, handleToggleAll } =
    usePaginatedPicker({
      selected,
      itemCount: totalRows,
      onChange: setSelected,
    });

  const handleSave = async () => {
    const payload = { ...monitor, databases: selected };
    const result = await putMonitorMutationTrigger(payload);
    toastResult(result);
    if (!isErrorResult(result)) {
      onClose();
    }
  };

  if (isLoading) {
    return <FidesSpinner />;
  }

  const saveIsDisabled = !allSelected && selected.length === 0;

  return (
    <>
      <Flex p={4} direction="column">
        <Flex direction="row" mb={4} gap={1} align="center">
          <Text fontSize="sm">Select projects to monitor</Text>
          <QuestionTooltip label={TOOLTIP_COPY} />
        </Flex>
        <MonitorDatabasePicker
          items={databases.map((d) => ({ name: d, id: d }))}
          itemCount={totalRows}
          selected={selected}
          allSelected={allSelected}
          someSelected={someSelected}
          handleToggleSelection={handleToggleSelection}
          handleToggleAll={handleToggleAll}
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
        <Tooltip
          label="Select one or more projects to save"
          isDisabled={!saveIsDisabled}
        >
          <Button
            onClick={handleSave}
            isLoading={isSubmitting}
            variant="primary"
            data-testid="save-btn"
            isDisabled={saveIsDisabled}
          >
            Save
          </Button>
        </Tooltip>
      </ButtonGroup>
    </>
  );
};

export default ConfigureMonitorDatabasesForm;
