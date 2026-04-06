import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  Button,
  Flex,
  Form,
  Icons,
  Input,
  Switch,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";
import DeleteUserModal from "user-management/DeleteUserModal";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import {
  selectPlusSecuritySettings,
  useGetConfigurationSettingsQuery,
} from "~/features/config-settings/config-settings.slice";
import { useGetEmailInviteStatusQuery } from "~/features/messaging/messaging.slice";
import { useGetAllOpenIDProvidersQuery } from "~/features/openid-authentication/openprovider.slice";
import { UserCreateExtended } from "~/types/api";

import PasswordManagement from "./PasswordManagement";
import { User, UserCreateResponse } from "./types";
import { passwordRules } from "~/features/common/form/validation";

import {
  shouldShowPasswordField,
  shouldShowPasswordLoginToggle,
  shouldShowPasswordManagement,
} from "./user-form-helpers";
import { selectActiveUser, setActiveUserId } from "./user-management.slice";

const { Text } = Typography;

export interface FormValues {
  username: string;
  first_name: string;
  email_address: string;
  last_name: string;
  password: string;
  password_login_enabled: boolean;
}

const defaultInitialValues: FormValues = {
  username: "",
  first_name: "",
  email_address: "",
  last_name: "",
  password: "",
  password_login_enabled: false,
};


export interface UserFormProps {
  onSubmit: (values: UserCreateExtended) => Promise<
    | {
        data: User | UserCreateResponse;
      }
    | {
        error: FetchBaseQueryError | SerializedError;
      }
  >;
  initialValues?: FormValues;
  canEditNames?: boolean;
}

const UserForm = ({ onSubmit, initialValues, canEditNames }: UserFormProps) => {
  // Hooks
  const router = useRouter();
  const message = useMessage();
  const dispatch = useAppDispatch();
  const [form] = Form.useForm<FormValues>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  // Watch form fields for reactive UI
  Form.useWatch([], form);

  // Queries
  const { data: emailInviteStatus } = useGetEmailInviteStatusQuery();
  const { data: openidProviders } = useGetAllOpenIDProvidersQuery();
  useGetConfigurationSettingsQuery({ api_set: false });

  // Selectors
  const activeUser = useAppSelector(selectActiveUser);
  const plusSecuritySettings = useAppSelector(selectPlusSecuritySettings);

  // Feature flags
  const { plus: isPlusEnabled } = useFeatures();

  // Derived state
  const inviteUsersViaEmail = emailInviteStatus?.enabled || false;
  const allowUsernameAndPassword =
    plusSecuritySettings?.allow_username_password_login || false;
  const isNewUser = !activeUser;
  const nameDisabled = isNewUser ? false : !canEditNames;
  const ssoEnabled = (openidProviders && openidProviders.length > 0) || false;

  const showPasswordLoginToggle = shouldShowPasswordLoginToggle(
    isPlusEnabled,
    ssoEnabled,
    allowUsernameAndPassword,
  );

  // Initialize form values from initialValues or defaults
  let formInitialValues = initialValues ?? defaultInitialValues;
  if (activeUser && "password_login_enabled" in activeUser) {
    formInitialValues = {
      ...formInitialValues,
      password_login_enabled: !!activeUser.password_login_enabled,
    };
  }

  const passwordLoginEnabled = Form.useWatch("password_login_enabled", form);

  const showPasswordField = shouldShowPasswordField(
    isNewUser,
    inviteUsersViaEmail,
    isPlusEnabled,
    ssoEnabled,
    allowUsernameAndPassword,
    passwordLoginEnabled,
  );

  const handleSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      // Determine which fields should be included based on current form state
      const includePassword = shouldShowPasswordField(
        isNewUser,
        inviteUsersViaEmail,
        isPlusEnabled,
        ssoEnabled,
        allowUsernameAndPassword,
        values.password_login_enabled,
      );

      // Create a clean payload
      const payload: UserCreateExtended = {
        username: values.username,
        email_address: values.email_address,
        first_name: values.first_name,
        last_name: values.last_name,
      };

      // Only include password_login_enabled if the toggle is shown
      if (showPasswordLoginToggle) {
        payload.password_login_enabled = values.password_login_enabled;
      }

      // Only include password if it should be shown
      if (includePassword && values.password) {
        payload.password = values.password;
      }

      const result = await onSubmit(payload);
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
        return;
      }
      message.success(
        `${
          isNewUser
            ? "User created. By default, new users are set to the Viewer role. To change the role, please go to the Permissions tab."
            : "User updated."
        }`,
      );
      if (result?.data) {
        dispatch(setActiveUserId(result.data.id));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={formInitialValues}
      onFinish={handleSubmit}
      data-testid="user-form"
      className="max-w-full"
    >
      <div className="flex max-w-[55%] flex-col">
        <Flex justify="space-between" align="center" className="mb-6">
          <Text className="flex items-center text-sm font-semibold">
            Profile{" "}
            {activeUser?.disabled && (
              <Tag
                color="success"
                className="ml-2"
                data-testid="invite-sent-badge"
              >
                Invite sent
              </Tag>
            )}
          </Text>
          <Flex gap={8}>
            {shouldShowPasswordManagement(
              isPlusEnabled,
              ssoEnabled,
              allowUsernameAndPassword || false,
              passwordLoginEnabled,
            ) && <PasswordManagement data-testid="password-management" />}
            {!isNewUser && (
              <>
                <Button
                  aria-label="delete"
                  icon={<Icons.TrashCan />}
                  onClick={() => setDeleteModalOpen(true)}
                  data-testid="delete-user-btn"
                />
                <DeleteUserModal
                  user={activeUser}
                  isOpen={deleteModalOpen}
                  onClose={() => setDeleteModalOpen(false)}
                />
              </>
            )}
          </Flex>
        </Flex>
        <Form.Item
          name="username"
          label="Username"
          rules={[{ required: true, message: "Username is required" }]}
        >
          <Input
            placeholder="Enter new username"
            disabled={!isNewUser}
            data-testid="input-username"
          />
        </Form.Item>
        <Form.Item
          name="email_address"
          label="Email address"
          rules={[
            { required: true, message: "Email address is required" },
            { type: "email", message: "Please enter a valid email address" },
          ]}
        >
          <Input
            placeholder="Enter email of user"
            data-testid="input-email-address"
          />
        </Form.Item>
        <Form.Item name="first_name" label="First name">
          <Input
            placeholder="Enter first name of user"
            disabled={nameDisabled}
            data-testid="input-first-name"
          />
        </Form.Item>
        <Form.Item name="last_name" label="Last name">
          <Input
            placeholder="Enter last name of user"
            disabled={nameDisabled}
            data-testid="input-last-name"
          />
        </Form.Item>
        {showPasswordLoginToggle && (
          <Form.Item
            name="password_login_enabled"
            label={
              <Flex align="center" gap={4}>
                Allow password login
                <InfoTooltip label="When enabled, user can log in with username and password. When disabled, user must use SSO." />
              </Flex>
            }
            valuePropName="checked"
          >
            <Switch
              disabled={!isNewUser}
              data-testid="toggle-allow-password-login"
            />
          </Form.Item>
        )}
        {showPasswordField && (
          <Form.Item
            name="password"
            label={
              <Flex align="center" gap={4}>
                Password
                <InfoTooltip label="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol." />
              </Flex>
            }
            rules={passwordRules}
          >
            <Input.Password
              placeholder="********"
              data-testid="input-password"
            />
          </Form.Item>
        )}
      </div>
      <div className="mt-7">
        <Button
          onClick={() => router.push(USER_MANAGEMENT_ROUTE)}
          className="mr-3"
          data-testid="cancel-btn"
        >
          Cancel
        </Button>
        <Button
          htmlType="submit"
          type="primary"
          disabled={
            !form.isFieldsTouched() ||
            form.getFieldsError().some(({ errors }) => errors.length > 0)
          }
          loading={isSubmitting}
          data-testid="save-user-btn"
        >
          Save
        </Button>
      </div>
    </Form>
  );
};

export default UserForm;
