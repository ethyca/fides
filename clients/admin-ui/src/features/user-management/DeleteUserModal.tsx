import {
  Alert,
  Button,
  Flex,
  Form,
  Input,
  Modal,
  Typography,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import React, { useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

import { User } from "./types";
import {
  setActiveUserId,
  useDeleteUserMutation,
} from "./user-management.slice";

const { Text } = Typography;

const useDeleteUserModal = ({
  id,
  username,
  onClose,
}: Pick<User, "id" | "username"> & { onClose: () => void }) => {
  const message = useMessage();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [deleteUser] = useDeleteUserMutation();

  const handleDeleteUser = async () => {
    const result = await deleteUser(id);
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success("Successfully deleted user");
      onClose();
    }
    dispatch(setActiveUserId(undefined));
    router.push(USER_MANAGEMENT_ROUTE);
  };

  return {
    handleDeleteUser,
    username,
  };
};

interface DeleteUserModalProps {
  user: User;
  isOpen: boolean;
  onClose: () => void;
}

const DeleteUserModal = ({ user, isOpen, onClose }: DeleteUserModalProps) => {
  const { handleDeleteUser, username } = useDeleteUserModal({
    id: user.id,
    username: user.username,
    onClose,
  });
  const [form] = Form.useForm();
  const [isSubmitting, setIsSubmitting] = useState(false);

  Form.useWatch([], form);

  const handleFinish = async () => {
    setIsSubmitting(true);
    try {
      await handleDeleteUser();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      data-testid="delete-user-modal"
      title="Delete User"
      centered
      destroyOnHidden
      footer={null}
    >
      <Form form={form} layout="vertical" onFinish={handleFinish}>
        <Alert
          type="warning"
          showIcon
          className="mb-4"
          description={
            <>
              <Text>You are about to delete the user&nbsp;</Text>
              <Text italic strong>
                {username}.
              </Text>
              <Text className="mt-2 block">
                This action cannot be undone. To confirm, please enter the
                user&rsquo;s username below.
              </Text>
            </>
          }
        />

        <Form.Item
          name="usernameConfirmation"
          label="Confirm username"
          rules={[
            { required: true, message: "Username confirmation is required" },
            {
              validator(_, value) {
                if (!value || value === username) {
                  return Promise.resolve();
                }
                return Promise.reject(
                  new Error("Confirmation input must match the username"),
                );
              },
            },
          ]}
        >
          <Input
            placeholder="Type the username to delete"
            data-testid="input-usernameConfirmation"
          />
        </Form.Item>

        <Flex className="mt-4 w-full" gap="small">
          <Button onClick={onClose} className="w-1/2">
            Cancel
          </Button>
          <Button
            type="primary"
            disabled={
              !form.isFieldsTouched(true) ||
              form.getFieldsError().some(({ errors }) => errors.length > 0)
            }
            loading={isSubmitting}
            htmlType="submit"
            className="w-1/2"
            data-testid="submit-btn"
          >
            Delete User
          </Button>
        </Flex>
      </Form>
    </Modal>
  );
};

export default DeleteUserModal;
