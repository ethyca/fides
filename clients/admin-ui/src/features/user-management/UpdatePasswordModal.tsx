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
  useToast,
} from "@fidesui/react";
import React, { useState } from "react";

import { successToastParams } from "../common/toast";
import { useUpdateUserPasswordMutation } from "./user-management.slice";

const useUpdatePasswordModal = (id: string) => {
  const modal = useDisclosure();
  const toast = useToast();
  const [oldPasswordValue, setOldPasswordValue] = useState("");
  const [newPasswordValue, setNewPasswordValue] = useState("");
  const [changePassword, { isLoading }] = useUpdateUserPasswordMutation();

  const changePasswordValidation = !!(
    id &&
    newPasswordValue &&
    oldPasswordValue
  );

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.name === "oldPassword") {
      setOldPasswordValue(event.target.value);
    } else {
      setNewPasswordValue(event.target.value);
    }
  };

  const handleChangePassword = async () => {
    if (changePasswordValidation) {
      changePassword({
        id,
        old_password: oldPasswordValue,
        new_password: newPasswordValue,
      })
        .unwrap()
        .then(() => {
          toast(successToastParams("Password updated"));
          modal.onClose();
        });
    }
  };

  return {
    ...modal,
    changePasswordValidation,
    handleChange,
    handleChangePassword,
    isLoading,
    newPasswordValue,
    oldPasswordValue,
  };
};

interface UpdatePasswordModalProps {
  id: string;
}

const UpdatePasswordModal: React.FC<UpdatePasswordModalProps> = ({ id }) => {
  const {
    changePasswordValidation,
    handleChange,
    handleChangePassword,
    isLoading,
    isOpen,
    newPasswordValue,
    oldPasswordValue,
    onClose,
    onOpen,
  } = useUpdatePasswordModal(id);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={onOpen}
        data-testid="update-password-btn"
      >
        Update password
      </Button>
      <Modal isCentered isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Update Password</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Stack direction="column" spacing="15px">
              <FormControl>
                <Input
                  isRequired
                  name="oldPassword"
                  onChange={handleChange}
                  placeholder="Old Password"
                  type="password"
                  value={oldPasswordValue}
                  data-testid="input-oldPassword"
                />
              </FormControl>
              <FormControl>
                <Input
                  isRequired
                  name="newPassword"
                  onChange={handleChange}
                  placeholder="New Password"
                  type="password"
                  value={newPasswordValue}
                  data-testid="input-newPassword"
                />
              </FormControl>
            </Stack>
          </ModalBody>

          <ModalFooter>
            <Button
              bg="white"
              marginRight="10px"
              onClick={onClose}
              size="sm"
              variant="solid"
              width="50%"
            >
              Cancel
            </Button>
            <Button
              bg="primary.800"
              color="white"
              disabled={!changePasswordValidation}
              isLoading={isLoading}
              mr={3}
              onClick={handleChangePassword}
              size="sm"
              type="submit"
              variant="solid"
              width="50%"
              data-testid="submit-btn"
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
