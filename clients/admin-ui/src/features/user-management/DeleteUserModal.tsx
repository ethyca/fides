import {
  Button,
  FormControl,
  Input,
  MenuItem,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useDisclosure,
} from '@fidesui/react';
import React, { useState } from 'react';

import { User } from '../user/types';
import { useDeleteUserMutation } from '../user/user.slice';

const DeleteUserModal = (user: User) => {
  const [usernameValue, setUsernameValue] = useState('');
  const [confirmValue, setConfirmValue] = useState('');
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [deleteUser,] = useDeleteUserMutation();

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.name === 'username') {
      setUsernameValue(event.target.value);
    } else {
      setConfirmValue(event.target.value);
    }
  };
  const {id: userId, username} = user;

  const deletionValidation =
    !!(userId &&
    confirmValue &&
    usernameValue &&
    username === usernameValue &&
    username === confirmValue);

  const handleDeleteUser = () => {
    if (deletionValidation && userId) {
      deleteUser(userId);
      onClose();
    }
  };

  return (
    <>
      <MenuItem
        _focus={{ color: 'complimentary.500', bg: 'gray.100' }}
        onClick={onOpen}
      >
        <Text fontSize="sm">Delete</Text>
      </MenuItem>
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Delete User</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Stack direction="column" spacing="15px">
              <FormControl>
                <Input
                  isRequired
                  name="username"
                  onChange={handleChange}
                  placeholder="Enter username"
                  value={usernameValue}
                />
              </FormControl>
              <FormControl>
                <Input
                  isRequired
                  name="confirmUsername"
                  onChange={handleChange}
                  placeholder="Confirm username"
                  value={confirmValue}
                />
              </FormControl>
            </Stack>
          </ModalBody>

          <ModalFooter>
            <Button
              onClick={onClose}
              marginRight="10px"
              size="sm"
              variant="solid"
              bg="white"
              width="50%"
            >
              Cancel
            </Button>
            <Button
              disabled={!deletionValidation}
              onClick={handleDeleteUser}
              mr={3}
              size="sm"
              variant="solid"
              bg="primary.800"
              color="white"
              width="50%"
            >
              Delete User
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}

export default DeleteUserModal;
