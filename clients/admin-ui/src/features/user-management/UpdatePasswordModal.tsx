import {
  AntButton as Button,
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
} from "fidesui";
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

const UpdatePasswordModal = ({ id }: UpdatePasswordModalProps) => {
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
      <Button onClick={onOpen} data-testid="update-password-btn">
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
            <Button onClick={onClose} className="mr-2 w-1/2">
              Cancel
            </Button>
            <Button
              type="primary"
              disabled={!changePasswordValidation}
              loading={isLoading}
              onClick={handleChangePassword}
              htmlType="submit"
              className="mr-3 w-1/2"
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
