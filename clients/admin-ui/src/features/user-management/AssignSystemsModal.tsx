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
  useToast,
} from "@fidesui/react";
import { ChangeEvent, useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import SearchBar from "~/features/common/SearchBar";
import { useGetAllSystemsQuery } from "~/features/system";
import { System } from "~/types/api";

import { getErrorMessage, isErrorResult } from "../common/helpers";
import { errorToastParams, successToastParams } from "../common/toast";
import AssignSystemsTable from "./AssignSystemsTable";
import {
  selectActiveUserId,
  selectActiveUsersManagedSystems,
  useGetUserManagedSystemsQuery,
  useUpdateUserManagedSystemsMutation,
} from "./user-management.slice";

const AssignSystemsModal = ({
  isOpen,
  onClose,
}: Pick<ModalProps, "isOpen" | "onClose">) => {
  const activeUserId = useAppSelector(selectActiveUserId);
  const { data: allSystems } = useGetAllSystemsQuery();
  useGetUserManagedSystemsQuery(activeUserId as string, {
    skip: !activeUserId,
  });
  const [updateUserManagedSystemsTrigger, { isLoading: isSubmitting }] =
    useUpdateUserManagedSystemsMutation();
  const [searchFilter, setSearchFilter] = useState("");
  const initialManagedSystems = useAppSelector(selectActiveUsersManagedSystems);
  const [assignedSystems, setAssignedSystems] = useState<System[]>(
    initialManagedSystems
  );
  const toast = useToast();

  useEffect(() => {
    setAssignedSystems(initialManagedSystems);
  }, [initialManagedSystems]);

  const handleAssign = async () => {
    if (!activeUserId) {
      return;
    }
    const fidesKeys = assignedSystems.map((s) => s.fides_key);
    const result = await updateUserManagedSystemsTrigger({
      userId: activeUserId,
      fidesKeys,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }
    toast(successToastParams("Updated users permissions"));
    onClose();
  };

  const emptySystems = !allSystems || allSystems.length === 0;
  const allSystemsAssigned = assignedSystems.length === allSystems?.length;

  const handleToggleAllSystems = (event: ChangeEvent<HTMLInputElement>) => {
    const { checked } = event.target;
    if (checked && allSystems) {
      setAssignedSystems(allSystems);
    } else {
      setAssignedSystems([]);
    }
  };

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
                    <Switch
                      size="sm"
                      id="assign-all-systems"
                      isChecked={allSystemsAssigned}
                      onChange={handleToggleAllSystems}
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
                isLoading={isSubmitting}
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
