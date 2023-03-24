import {
  Badge,
  Box,
  Button,
  ButtonGroup,
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
  Switch,
  Text,
} from "@fidesui/react";
import { ChangeEvent, useMemo, useState } from "react";

import SearchBar from "~/features/common/SearchBar";
import { useGetAllSystemsQuery } from "~/features/system";
import { SEARCH_FILTER } from "~/features/system/SystemsManagement";
import { System } from "~/types/api";

import AssignSystemsTable from "./AssignSystemsTable";

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

  const handleToggleAllSystems = (event: ChangeEvent<HTMLInputElement>) => {
    const { checked } = event.target;
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
          <Badge bg="green.500" color="white" px={1}>
            Assigned to {assignedSystems.length} systems
          </Badge>
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
                      size="sm"
                      id="assign-all-systems"
                      isChecked={allSystemsAssigned}
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
          <ButtonGroup size="sm">
            <Button
              variant="outline"
              mr={2}
              onClick={onClose}
              data-testid="cancel-btn"
            >
              Cancel
            </Button>
            {!emptySystems ? (
              <Button
                colorScheme="primary"
                onClick={handleConfirm}
                data-testid="confirm-btn"
              >
                Confirm
              </Button>
            ) : null}
          </ButtonGroup>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default AssignSystemsModal;
