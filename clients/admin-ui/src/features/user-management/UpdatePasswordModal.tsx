import { Button, Flex, Input, Modal, useMessage } from "fidesui";
import { useRouter } from "next/router";
import React, { useState } from "react";
import { useDispatch } from "react-redux";

import { clearAuthAndLogout } from "./logout-helpers";
import { useUpdateUserPasswordMutation } from "./user-management.slice";

const useUpdatePasswordModal = (id: string) => {
  const [isOpen, setIsOpen] = useState(false);
  const message = useMessage();
  const [oldPasswordValue, setOldPasswordValue] = useState("");
  const [newPasswordValue, setNewPasswordValue] = useState("");
  const [changePassword, { isLoading }] = useUpdateUserPasswordMutation();
  const router = useRouter();
  const dispatch = useDispatch();

  const changePasswordValidation = !!(
    id &&
    newPasswordValue &&
    oldPasswordValue
  );

  const handleChangePassword = async () => {
    if (changePasswordValidation) {
      changePassword({
        id,
        old_password: oldPasswordValue,
        new_password: newPasswordValue,
      })
        .unwrap()
        .then(() => {
          message.success("Password updated");
          clearAuthAndLogout(dispatch as any, router, {
            onClose: () => setIsOpen(false),
          });
        });
    }
  };

  return {
    isOpen,
    onOpen: () => setIsOpen(true),
    onClose: () => setIsOpen(false),
    changePasswordValidation,
    oldPasswordValue,
    setOldPasswordValue,
    newPasswordValue,
    setNewPasswordValue,
    handleChangePassword,
    isLoading,
  };
};

interface UpdatePasswordModalProps {
  id: string;
}

const UpdatePasswordModal = ({ id }: UpdatePasswordModalProps) => {
  const {
    changePasswordValidation,
    oldPasswordValue,
    setOldPasswordValue,
    newPasswordValue,
    setNewPasswordValue,
    handleChangePassword,
    isLoading,
    isOpen,
    onClose,
    onOpen,
  } = useUpdatePasswordModal(id);

  return (
    <>
      <Button onClick={onOpen} data-testid="update-password-btn">
        Update password
      </Button>
      <Modal
        open={isOpen}
        onCancel={onClose}
        title="Update Password"
        centered
        destroyOnHidden
        footer={
          <>
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
          </>
        }
      >
        <Flex vertical gap={15}>
          <Input.Password
            name="oldPassword"
            onChange={(e) => setOldPasswordValue(e.target.value)}
            placeholder="Old Password"
            value={oldPasswordValue}
            data-testid="input-oldPassword"
          />
          <Input.Password
            name="newPassword"
            onChange={(e) => setNewPasswordValue(e.target.value)}
            placeholder="New Password"
            value={newPasswordValue}
            data-testid="input-newPassword"
          />
        </Flex>
      </Modal>
    </>
  );
};

export default UpdatePasswordModal;
