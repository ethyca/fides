import {
  AntButton as Button,
  AntSwitch as Switch,
  AntTag as Tag,
  Box,
  Flex,
  FormControl,
  FormLabel,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  ModalProps,
  Stack,
  Text,
} from "fidesui";
import { useMemo, useState } from "react";

import SearchBar from "~/features/common/SearchBar";
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
}: Pick<ModalProps, "isOpen" | "onClose"> & {
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
    <Modal isOpen={isOpen} onClose={onClose} size="2xl">
      <ModalOverlay />
      <ModalContent p={8} data-testid="confirmation-modal">
        <ModalHeader
          fontWeight="medium"
          display="flex"
          justifyContent="space-between"
          alignItems="center"
        >
          <Text>Assign systems</Text>
          <Tag color="success">
            Assigned to {assignedSystems.length} systems
          </Tag>
        </ModalHeader>
        <ModalBody data-testid="assign-systems-modal-body">
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
                    <FormLabel
                      fontSize="sm"
                      htmlFor="assign-all-systems"
                      mb="0"
                    >
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
              <SearchBar
                search={searchFilter}
                onChange={setSearchFilter}
                placeholder="Search for systems"
                data-testid="system-search"
                withIcon
              />
              <AssignSystemsTable
                allSystems={filteredSystems}
                assignedSystems={selectedSystems}
                onChange={setSelectedSystems}
              />
            </Stack>
          )}
        </ModalBody>
        <ModalFooter justifyContent="flex-start">
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
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default AssignSystemsModal;
