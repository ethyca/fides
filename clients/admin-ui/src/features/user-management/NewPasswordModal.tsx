import {
  Button,
  Flex,
  Form,
  Input,
  Modal,
  Typography,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth/auth.slice";
import { getErrorMessage } from "~/features/common/helpers";
import { isErrorResult } from "~/types/errors";

import { clearAuthAndLogout } from "./logout-helpers";
import { useForceResetUserPasswordMutation } from "./user-management.slice";

const { Text } = Typography;

interface FormValues {
  password: string;
  passwordConfirmation: string;
}

const passwordRules = [
  { required: true, message: "Password is required" },
  { min: 8, message: "Password must have at least eight characters." },
  { pattern: /[0-9]/, message: "Password must have at least one number." },
  {
    pattern: /[A-Z]/,
    message: "Password must have at least one capital letter.",
  },
  {
    pattern: /[a-z]/,
    message: "Password must have at least one lowercase letter.",
  },
  { pattern: /[\W_]/, message: "Password must have at least one symbol." },
];

const useNewPasswordModal = (id: string) => {
  const [isOpen, setIsOpen] = useState(false);
  const message = useMessage();
  const [resetPassword] = useForceResetUserPasswordMutation();
  const router = useRouter();
  const dispatch = useDispatch();
  const currentUser = useAppSelector(selectUser);

  const handleResetPassword = async (values: FormValues) => {
    const result = await resetPassword({
      id,
      new_password: values.password,
    });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success(
        "Successfully reset user's password. Please inform the user of their new password.",
      );
      setIsOpen(false);

      // Only logout if admin reset their own password
      if (currentUser?.id === id) {
        clearAuthAndLogout(dispatch as any, router);
      }
    }
  };

  return {
    isOpen,
    onOpen: () => setIsOpen(true),
    onClose: () => setIsOpen(false),
    handleResetPassword,
  };
};

interface Props {
  id: string;
}

const NewPasswordModal = ({ id }: Props) => {
  const { handleResetPassword, isOpen, onClose, onOpen } =
    useNewPasswordModal(id);
  const [form] = Form.useForm<FormValues>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  Form.useWatch([], form);

  const handleFinish = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      await handleResetPassword(values);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Button onClick={onOpen} data-testid="reset-password-btn">
        Reset password
      </Button>
      <Modal
        open={isOpen}
        onCancel={onClose}
        title="Reset Password"
        centered
        destroyOnHidden
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleFinish}>
          <Text className="mb-2 block">
            Choose a new password for this user.
          </Text>
          <Form.Item
            name="password"
            label="Password"
            tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
            rules={passwordRules}
          >
            <Input.Password
              placeholder="********"
              autoComplete="new-password"
            />
          </Form.Item>
          <Form.Item
            name="passwordConfirmation"
            label="Confirm Password"
            tooltip="Must match above password."
            dependencies={["password"]}
            rules={[
              { required: true, message: "Password confirmation is required" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("Passwords must match"));
                },
              }),
            ]}
          >
            <Input.Password
              placeholder="********"
              autoComplete="confirm-password"
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
              Change Password
            </Button>
          </Flex>
        </Form>
      </Modal>
    </>
  );
};

export default NewPasswordModal;
