import {
  Button,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraFormControl as FormControl,
  ChakraFormLabel as FormLabel,
  ChakraStack as Stack,
  ChakraText as Text,
  Modal,
  Switch,
  Tag,
} from "fidesui";
import { useFormikContext } from "formik";
import { useMemo, useState } from "react";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import SearchInput from "~/features/common/SearchInput";
import { DataFlow, System } from "~/types/api";

import DataFlowSystemsTable from "./DataFlowSystemsTable";

type Props = {
  currentSystem: System;
  systems: System[];
  dataFlowSystems: DataFlow[];
  onDataFlowSystemChange: (systems: DataFlow[]) => void;
  flowType: string;
};

export const SEARCH_FILTER = (system: System, search: string) =>
  system.name?.toLocaleLowerCase().includes(search.toLocaleLowerCase()) ||
  system.description?.toLocaleLowerCase().includes(search.toLocaleLowerCase());

const DataFlowSystemsModal = ({
  currentSystem,
  systems,
  isOpen,
  onClose,
  dataFlowSystems,
  onDataFlowSystemChange,
  flowType,
}: { isOpen: boolean; onClose: () => void } & Props) => {
  const { setFieldValue } = useFormikContext();
  const [searchFilter, setSearchFilter] = useState("");
  const [selectedDataFlows, setSelectedDataFlows] =
    useState<DataFlow[]>(dataFlowSystems);

  const handleConfirm = async () => {
    onDataFlowSystemChange(selectedDataFlows);
    onClose();
  };

  const emptySystems = systems.length === 0;

  const filteredSystems = useMemo(() => {
    if (!systems) {
      return [];
    }

    return systems
      .filter((system) => system.fides_key !== currentSystem.fides_key)
      .filter((s) => SEARCH_FILTER(s, searchFilter));
  }, [systems, currentSystem.fides_key, searchFilter]);

  const handleToggleAllSystems = (checked: boolean) => {
    if (checked && systems) {
      const updatedDataFlows = filteredSystems.map((fs) => ({
        fides_key: fs.fides_key,
        type: "system",
      }));

      setFieldValue("dataFlowSystems", updatedDataFlows);
      setSelectedDataFlows(updatedDataFlows);
    } else {
      setSelectedDataFlows([]);
    }
  };

  const allSystemsAssigned = useMemo(() => {
    const assignedSet = new Set(selectedDataFlows.map((s) => s.fides_key));
    return filteredSystems.every((item) => assignedSet.has(item.fides_key));
  }, [filteredSystems, selectedDataFlows]);

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      width={MODAL_SIZE.md}
      centered
      destroyOnClose
      data-testid="confirmation-modal"
      title={
        <div className="flex items-center justify-between pr-6">
          <span>Configure {flowType.toLocaleLowerCase()} systems</span>
          <Tag color="success">
            Assigned to {selectedDataFlows.length} systems
          </Tag>
        </div>
      }
      footer={
        <div className="flex justify-start gap-2">
          <Button onClick={onClose} className="mr-2" data-testid="cancel-btn">
            Cancel
          </Button>
          {!emptySystems && (
            <Button
              type="primary"
              onClick={handleConfirm}
              data-testid="confirm-btn"
            >
              Confirm
            </Button>
          )}
        </div>
      }
    >
      <div data-testid="assign-systems-modal-body">
        {emptySystems ? (
          <Text>No systems found</Text>
        ) : (
          <Stack spacing={4}>
            <Flex justifyContent="space-between">
              <Text fontSize="sm" flexGrow={1} fontWeight="medium">
                Add or remove destination systems from your data map
              </Text>
              <Box>
                <FormControl display="flex" alignItems="center">
                  <FormLabel fontSize="sm" htmlFor="assign-all-systems" mb="0">
                    Assign all systems
                  </FormLabel>
                  <Switch
                    size="small"
                    id="assign-all-systems"
                    checked={allSystemsAssigned}
                    onChange={handleToggleAllSystems}
                    data-testid="assign-all-systems-toggle"
                  />
                </FormControl>
              </Box>
            </Flex>
            <SearchInput
              value={searchFilter}
              onChange={setSearchFilter}
              placeholder="Search for systems"
              data-testid="system-search"
            />
            <DataFlowSystemsTable
              flowType={flowType}
              allSystems={filteredSystems}
              dataFlowSystems={selectedDataFlows}
              onChange={setSelectedDataFlows}
            />
          </Stack>
        )}
      </div>
    </Modal>
  );
};

export default DataFlowSystemsModal;
