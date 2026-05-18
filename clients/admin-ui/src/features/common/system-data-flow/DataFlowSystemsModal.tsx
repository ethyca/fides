import { Button, Flex, Form, Modal, Switch, Tag, Text } from "fidesui";
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
      destroyOnHidden
      data-testid="confirmation-modal"
      title={
        <Flex align="center" justify="space-between" className="pr-6">
          <span>Configure {flowType.toLocaleLowerCase()} systems</span>
          <Tag color="success">
            Assigned to {selectedDataFlows.length} systems
          </Tag>
        </Flex>
      }
      footer={
        <Flex justify="flex-start" gap="small">
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
        </Flex>
      }
    >
      <div data-testid="assign-systems-modal-body">
        {emptySystems ? (
          <Text>No systems found</Text>
        ) : (
          <Flex vertical gap="large">
            <Flex justify="space-between" align="center">
              <Text className="flex-1 text-sm font-medium">
                Add or remove destination systems from your data map
              </Text>
              <Form.Item label="Assign all systems" className="mb-0">
                <Switch
                  size="small"
                  checked={allSystemsAssigned}
                  onChange={handleToggleAllSystems}
                  data-testid="assign-all-systems-toggle"
                />
              </Form.Item>
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
          </Flex>
        )}
      </div>
    </Modal>
  );
};

export default DataFlowSystemsModal;
