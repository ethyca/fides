import {
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
import { useState } from "react";

import SearchBar from "~/features/common/SearchBar";
import { useGetAllSystemsQuery } from "~/features/system";
import { System } from "~/types/api";

import AssignSystemsTable from "./AssignSystemsTable";

const AssignSystemsModal = ({
  isOpen,
  onClose,
}: Pick<ModalProps, "isOpen" | "onClose">) => {
  const { data: allSystems } = useGetAllSystemsQuery();
  const [searchFilter, setSearchFilter] = useState("");
  const [assignedSystems, setAssignedSystems] = useState<System[]>([]);
  const handleAssign = () => {};

  const emptySystems = !allSystems || allSystems.length === 0;

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="2xl">
      <ModalOverlay />
      <ModalContent p={8} data-testid="confirmation-modal">
        <ModalHeader fontWeight="medium">Assign systems</ModalHeader>
        <ModalBody>
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
                    <Switch size="sm" id="assign-all-systems" />
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
                allSystems={allSystems}
                assignedSystems={assignedSystems}
                onChange={setAssignedSystems}
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
                onClick={handleAssign}
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
