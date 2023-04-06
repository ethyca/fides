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

import SearchBar from "common/SearchBar";
import { useGetAllSystemsQuery } from "~/features/system";
import { SEARCH_FILTER } from "~/features/system/SystemsManagement";
import { DataFlow } from "~/types/api";

import DataFlowSystemsTable from "./DataFlowSystemsTable";
import { useFormikContext } from "formik";

type Props = {
  dataFlowSystems: DataFlow[];
  onDataFlowSystemChange: (systems: DataFlow[]) => void;
};

const DataFlowSystemsModal = ({
  isOpen,
  onClose,
  dataFlowSystems,
  onDataFlowSystemChange,
}: Pick<ModalProps, "isOpen" | "onClose"> & Props) => {
  const { setFieldValue } = useFormikContext();
  const { data: allSystems } = useGetAllSystemsQuery();
  const [searchFilter, setSearchFilter] = useState("");
  const [selectedDataFlows, setSelectedDataFlows] =
    useState<DataFlow[]>(dataFlowSystems);

  const handleConfirm = async () => {
    onDataFlowSystemChange(selectedDataFlows);
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
    console.log("recalcing all systems assigned");
    const assignedSet = new Set(selectedDataFlows.map((s) => s.fides_key));
    return filteredSystems.every((item) => assignedSet.has(item.fides_key));
  }, [filteredSystems, selectedDataFlows]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="2xl" isCentered>
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
            Assigned to {selectedDataFlows.length} systems
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
              <DataFlowSystemsTable
                allSystems={filteredSystems}
                dataFlowSystems={selectedDataFlows}
                onChange={setSelectedDataFlows}
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

export default DataFlowSystemsModal;
