import {
  Box,
  Heading,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
  Text,
  useDisclosure,
  useToast,
} from "@fidesui/react";
import { useRouter } from "next/router";

import { useAppDispatch } from "~/app/hooks";
import { SYSTEM_ROUTE } from "~/constants";
import ConfirmationModal from "~/features/common/ConfirmationModal";
import { System } from "~/types/api";

import { getErrorMessage, isErrorResult } from "../common/helpers";
import { errorToastParams, successToastParams } from "../common/toast";
import { setActiveSystem, useDeleteSystemMutation } from "./system.slice";

interface SystemCardProps {
  system: System;
}
const SystemCard = ({ system }: SystemCardProps) => {
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  const toast = useToast();
  const dispatch = useAppDispatch();
  const router = useRouter();

  const [deleteSystem] = useDeleteSystemMutation();

  const handleEdit = () => {
    dispatch(setActiveSystem(system));
    router.push(`${SYSTEM_ROUTE}/configure`);
  };

  const handleDelete = async () => {
    const result = await deleteSystem(system.fides_key);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Successfully deleted system"));
    }
    onDeleteClose();
  };

  const systemName =
    system.name === "" || system.name == null ? system.fides_key : system.name;

  return (
    <Box display="flex" data-testid={`system-${system.fides_key}`}>
      <Box flexGrow={1} p={4}>
        <Heading as="h2" fontSize="16px" mb={2}>
          {systemName}
        </Heading>
        <Box color="gray.600" fontSize="14px">
          <Text>{system.description}</Text>
        </Box>
      </Box>
      <Menu>
        <MenuButton
          as={IconButton}
          icon={<MoreIcon />}
          aria-label="more actions"
          variant="unstyled"
          size="sm"
          data-testid="more-btn"
          m={1}
        />
        <MenuList>
          <MenuItem onClick={handleEdit} data-testid="edit-btn">
            Edit
          </MenuItem>
          <MenuItem onClick={onDeleteOpen} data-testid="delete-btn">
            Delete
          </MenuItem>
        </MenuList>
      </Menu>
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title={`Delete ${systemName}`}
        message={
          <>
            <Text>
              You are about to permanently delete the system{" "}
              <Text color="complimentary.500" as="span" fontWeight="bold">
                {systemName}
              </Text>
              .
            </Text>
            <Text>Are you sure you would like to continue?</Text>
          </>
        }
      />
    </Box>
  );
};

export default SystemCard;
