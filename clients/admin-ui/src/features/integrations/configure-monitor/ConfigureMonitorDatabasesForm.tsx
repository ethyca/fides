import { AntButton as Button, Flex, Text, Tooltip, useToast } from "fidesui";

import FidesSpinner from "~/features/common/FidesSpinner";
import { usePaginatedPicker } from "~/features/common/hooks/usePicker";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import MonitorDatabasePicker from "~/features/integrations/configure-monitor/MonitorDatabasePicker";
import useCumulativeGetDatabases from "~/features/integrations/configure-monitor/useCumulativeGetDatabases";
import { MonitorConfig } from "~/types/api";

const TOOLTIP_COPY =
  "Selecting a project will monitor all current and future datasets within that project.";
const ConfigureMonitorDatabasesForm = ({
  monitor,
  isEditing,
  isSubmitting,
  integrationKey,
  onSubmit,
  onClose,
}: {
  monitor: MonitorConfig;
  isEditing?: boolean;
  isSubmitting?: boolean;
  integrationKey: string;
  onSubmit: (monitor: MonitorConfig) => void;
  onClose: () => void;
}) => {
  const toast = useToast();

  const handleTimeout = () => {
    onSubmit({ ...monitor, databases: [] });
    toast({
      ...DEFAULT_TOAST_PARAMS,
      status: "info",
      description:
        "Loading projects to narrow scope of this monitor is taking a long time, usually because many projects are available.  The monitor has been saved without a set scope and will monitor all available projects.",
    });
  };

  const {
    databases,
    totalDatabases: totalRows,
    fetchMore,
    reachedEnd,
    isLoading: refetchPending,
    initialIsLoading,
  } = useCumulativeGetDatabases(integrationKey, handleTimeout);

  const initialSelected = monitor?.databases ?? [];

  const {
    selected,
    excluded,
    allSelected,
    someSelected,
    handleToggleItemSelected,
    handleToggleAll,
  } = usePaginatedPicker({
    initialSelected,
    initialExcluded: [],
    initialAllSelected: isEditing && !initialSelected.length,
    itemCount: totalRows,
  });

  const handleSave = () => {
    const payload = {
      ...monitor,
      excluded_databases: excluded,
      databases: allSelected ? [] : selected,
    };
    onSubmit(payload);
  };

  const saveIsDisabled = !allSelected && selected.length === 0;

  if (initialIsLoading) {
    return <FidesSpinner my={12} />;
  }

  return (
    <>
      <Flex p={4} direction="column">
        <Flex direction="row" mb={4} gap={1} align="center">
          <Text fontSize="sm">Select projects to monitor</Text>
          <QuestionTooltip label={TOOLTIP_COPY} />
        </Flex>
        <MonitorDatabasePicker
          items={databases}
          totalItemCount={totalRows}
          selected={selected}
          excluded={excluded}
          allSelected={allSelected}
          someSelected={someSelected}
          moreLoading={refetchPending}
          handleToggleSelection={handleToggleItemSelected}
          handleToggleAll={handleToggleAll}
          onMoreClick={!reachedEnd ? fetchMore : undefined}
        />
      </Flex>
      <div className="mt-4 flex w-full justify-between">
        <Button onClick={onClose}>Cancel</Button>
        <Tooltip
          label="Select one or more projects to save"
          isDisabled={!saveIsDisabled}
        >
          <Button
            onClick={handleSave}
            loading={isSubmitting}
            type="primary"
            data-testid="save-btn"
            disabled={saveIsDisabled}
          >
            Save
          </Button>
        </Tooltip>
      </div>
    </>
  );
};

export default ConfigureMonitorDatabasesForm;
