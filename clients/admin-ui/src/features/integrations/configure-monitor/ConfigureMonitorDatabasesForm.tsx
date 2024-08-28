import { Button, ButtonGroup, Flex, Text, Tooltip } from "fidesui";

import { usePaginatedPicker } from "~/features/common/hooks/usePicker";
import QuestionTooltip from "~/features/common/QuestionTooltip";
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
  const {
    databases,
    totalDatabases: totalRows,
    fetchMore,
    reachedEnd,
    isLoading: refetchPending,
  } = useCumulativeGetDatabases(integrationKey);

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
