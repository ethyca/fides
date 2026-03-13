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
import { useMemo, useState } from "react";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import SearchInput from "~/features/common/SearchInput";
import { useGetAllSystemsQuery } from "~/features/system";
import { System } from "~/types/api";

import AssignSystemsTable from "./AssignSystemsTable";

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
  const { data: allSystems } = useGetAllSystemsQuery();
  const [searchFilter, setSearchFilter] = useState("");
  const [selectedSystems, setSelectedSystems] =
    useState<System[]>(assignedSystems);

  const handleConfirm = async () => {
    onAssignedSystemChange(selectedSystems);
    onClose();
  };

  const emptySystems = !allSystems || allSystems.length === 0;

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
          <Stack spacing={4}>
            <Flex justifyContent="space-between">
              <Text fontSize="sm" flexGrow={1} fontWeight="medium">
                Assign systems in your organization to this user
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
            <AssignSystemsTable
              allSystems={filteredSystems}
              assignedSystems={selectedSystems}
              onChange={setSelectedSystems}
            />
          </Stack>
        )}
      </div>
    </Modal>
  );
};

export default AssignSystemsModal;
