import { Button, Flex, Modal, Switch, Tag, Typography } from "fidesui";
import { useMemo, useState } from "react";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import SearchInput from "~/features/common/SearchInput";
import { useGetAllSystemsQuery } from "~/features/system";
import { System } from "~/types/api";

import AssignSystemsTable from "./AssignSystemsTable";

const { Text } = Typography;

export const SEARCH_FILTER = (system: System, search: string) =>
  system.name?.toLocaleLowerCase().includes(search.toLocaleLowerCase()) ||
  system.description?.toLocaleLowerCase().includes(search.toLocaleLowerCase());

const AssignSystemsModal = ({
  isOpen,
  onClose,
  assignedSystems,
  onAssignedSystemChange,
}: {
  isOpen: boolean;
  onClose: () => void;
  assignedSystems: System[];
  onAssignedSystemChange: (systems: System[]) => void;
}) => {
  const { data: allSystems, isLoading } = useGetAllSystemsQuery();
  const [searchFilter, setSearchFilter] = useState("");
  const [selectedSystems, setSelectedSystems] =
    useState<System[]>(assignedSystems);

  const handleConfirm = async () => {
    onAssignedSystemChange(selectedSystems);
    onClose();
  };

  const emptySystems = (!allSystems || allSystems.length === 0) && !isLoading;

  const filteredSystems = useMemo(() => {
    if (!allSystems) {
      return [];
    }

    return allSystems.filter((s) => SEARCH_FILTER(s, searchFilter));
  }, [allSystems, searchFilter]);

  const handleToggleAllSystems = (checked: boolean) => {
    if (checked && allSystems) {
      setSelectedSystems(filteredSystems);
    } else {
      const notFilteredSystems = allSystems
        ? allSystems.filter((system) => !filteredSystems.includes(system))
        : [];
      setSelectedSystems(notFilteredSystems);
    }
  };

  const allSystemsAssigned = useMemo(() => {
    const assignedSet = new Set(selectedSystems.map((s) => s.fides_key));
    return filteredSystems.every((item) => assignedSet.has(item.fides_key));
  }, [filteredSystems, selectedSystems]);

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      data-testid="confirmation-modal"
      title={
        <Flex align="center" justify="space-between" className="pr-6">
          <span>Assign systems</span>
          <Tag color="success">
            Assigned to {assignedSystems.length} systems
          </Tag>
        </Flex>
      }
      centered
      destroyOnHidden
      width={MODAL_SIZE.md}
      footer={
        <div>
          <Button onClick={onClose} className="mr-2" data-testid="cancel-btn">
            Cancel
          </Button>
          {!emptySystems ? (
            <Button
              type="primary"
              onClick={handleConfirm}
              data-testid="confirm-btn"
            >
              Confirm
            </Button>
          ) : null}
        </div>
      }
    >
      <div data-testid="assign-systems-modal-body">
        {emptySystems ? (
          <Text>No systems found</Text>
        ) : (
          <Flex vertical gap={16}>
            <Flex justify="space-between" align="center">
              <Text className="flex-1 text-sm font-medium">
                Assign systems in your organization to this user
              </Text>
              <Flex align="center" gap={8}>
                <Text className="text-sm">Assign all systems</Text>
                <Switch
                  size="small"
                  id="assign-all-systems"
                  checked={allSystemsAssigned}
                  onChange={handleToggleAllSystems}
                  data-testid="assign-all-systems-toggle"
                />
              </Flex>
            </Flex>
            <SearchInput
              value={searchFilter}
              onChange={setSearchFilter}
              placeholder="Search for systems"
              data-testid="system-search"
            />
            <AssignSystemsTable
              allSystems={filteredSystems}
              assignedSystems={selectedSystems}
              isLoading={isLoading}
              onChange={setSelectedSystems}
            />
          </Flex>
        )}
      </div>
    </Modal>
  );
};

export default AssignSystemsModal;
