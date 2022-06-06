import {
  Button,
  FormControl,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  useDisclosure,
} from '@fidesui/react';
import React, { useState } from 'react';

import { useUpdateUserPasswordMutation } from '../user/user.slice';

const UpdatePasswordModal = ({ id }: { id: string }) => {
  const [oldPasswordValue, setOldPasswordValue] = useState('');
  const [newPasswordValue, setNewPasswordValue] = useState('');
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [changePassword] = useUpdateUserPasswordMutation();

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.name === 'oldPassword') {
      setOldPasswordValue(event.target.value);
    } else {
      setNewPasswordValue(event.target.value);
    }
  };

  const changePasswordValidation = !!(
    id &&
    newPasswordValue &&
    oldPasswordValue
  );

  const handleChangePassword = () => {
    if (changePasswordValidation) {
      const changePasswordBody = {
        id,
        old_password: oldPasswordValue,
        new_password: newPasswordValue,
      };

      changePassword(changePasswordBody);

      onClose();
    }
  };

  return (
    <>
      <Button
        bg='primary.800'
        _hover={{ bg: 'primary.400' }}
        _active={{ bg: 'primary.500' }}
        colorScheme='primary'
        maxWidth='40%'
        size='sm'
        onClick={onOpen}
      >
        Update Password
      </Button>
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Update Password</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Stack direction='column' spacing='15px'>
              <FormControl>
                <Input
                  isRequired
                  name='oldPassword'
                  onChange={handleChange}
                  placeholder='Old Password'
                  type='password'
                  value={oldPasswordValue}
                />
              </FormControl>
              <FormControl>
                <Input
                  isRequired
                  name='newPassword'
                  onChange={handleChange}
                  placeholder='New Password'
                  type='password'
                  value={newPasswordValue}
                />
              </FormControl>
            </Stack>
          </ModalBody>

          <ModalFooter>
            <Button
              onClick={onClose}
              marginRight='10px'
              size='sm'
              variant='solid'
              bg='white'
              width='50%'
            >
              Cancel
            </Button>
            <Button
              disabled={!changePasswordValidation}
              onClick={handleChangePassword}
              mr={3}
              size='sm'
              variant='solid'
              bg='primary.800'
              color='white'
              width='50%'
            >
              Change Password
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default UpdatePasswordModal;
