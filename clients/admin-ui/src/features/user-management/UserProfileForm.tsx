import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  Alert,
  Button,
  Flex,
  Form,
  Input,
  Modal,
  Switch,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  passwordRules,
  usernameRules,
} from "~/features/common/form/validation";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useHasPermission } from "~/features/common/Restrict";
import {
  selectPlusSecuritySettings,
  useGetConfigurationSettingsQuery,
} from "~/features/config-settings/config-settings.slice";
import { useGetEmailInviteStatusQuery } from "~/features/messaging/messaging.slice";
import { useGetAllOpenIDProvidersQuery } from "~/features/openid-authentication/openprovider.slice";
import { ScopeRegistryEnum, UserCreateExtended } from "~/types/api";

import PasswordManagement from "./PasswordManagement";
import { User, UserCreateResponse } from "./types";
import {
  shouldShowPasswordField,
  shouldShowPasswordLoginToggle,
  shouldShowPasswordManagement,
} from "./user-form-helpers";
import { useReinviteUserMutation } from "./user-management.slice";

const { Text } = Typography;

export interface ProfileFormValues {
  username: string;
  first_name: string;
  email_address: string;
  last_name: string;
  password: string;
  password_login_enabled: boolean;
}

const defaultInitialValues: ProfileFormValues = {
  username: "",
  first_name: "",
  email_address: "",
  last_name: "",
  password: "",
  password_login_enabled: false,
};

interface UserProfileFormProps {
  user?: User;
  onSubmit: (values: UserCreateExtended) => Promise<
    | { data: User | UserCreateResponse }
    | { error: FetchBaseQueryError | SerializedError }
  >;
  canEditNames?: boolean;
}

const UserProfileForm = ({
  user,
  onSubmit,
  canEditNames,
}: UserProfileFormProps) => {
  const message = useMessage();
  const [form] = Form.useForm<ProfileFormValues>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Watch form fields for reactive UI
  Form.useWatch([], form);

  // Queries
  const { data: emailInviteStatus } = useGetEmailInviteStatusQuery();
  const { data: openidProviders } = useGetAllOpenIDProvidersQuery();
  useGetConfigurationSettingsQuery({ api_set: false });

  // Selectors
  const plusSecuritySettings = useAppSelector(selectPlusSecuritySettings);

  // Feature flags
  const { plus: isPlusEnabled } = useFeatures();

  // Derived state
  const inviteUsersViaEmail = emailInviteStatus?.enabled || false;
  const allowUsernameAndPassword =
    plusSecuritySettings?.allow_username_password_login || false;
  const isNewUser = !user;
  const nameDisabled = isNewUser ? false : !canEditNames;
  const ssoEnabled = (openidProviders && openidProviders.length > 0) || false;

  const showPasswordLoginToggle = shouldShowPasswordLoginToggle(
    isPlusEnabled,
    ssoEnabled,
    allowUsernameAndPassword,
  );

  // Build initial values
  let formInitialValues: ProfileFormValues;
  if (user) {
    formInitialValues = {
      username: user.username ?? "",
      email_address: user.email_address ?? "",
      first_name: user.first_name ?? "",
      last_name: user.last_name ?? "",
      password: "",
      password_login_enabled: !!user.password_login_enabled,
    };
  } else {
    formInitialValues = defaultInitialValues;
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

  // Reinvite
  const [reinviteUser, { isLoading: isReinviting }] =
    useReinviteUserMutation();
  const [modal, contextHolder] = Modal.useModal();
  const canReinvite = useHasPermission([ScopeRegistryEnum.USER_CREATE]);

  const handleReinviteClick = () => {
    if (!user) return;
    modal.confirm({
      title: "Reinvite user",
      content: (
        <>
          <p>
            Are you sure you want to send a new invitation to {user.username}?
            {user.email_address
              ? ` A new invitation email will be sent to ${user.email_address}.`
              : ""}
          </p>
          {!user.invite_expired ? (
            <p>The previous invitation code will no longer be valid.</p>
          ) : null}
        </>
      ),
      okText: "Reinvite",
      cancelText: "Cancel",
      onOk: async () => {
        try {
          await reinviteUser(user.id).unwrap();
          message.success("User reinvited successfully.");
        } catch (error) {
          message.error(getErrorMessage(error));
        }
      },
    });
  };

  const handleSubmit = async (values: ProfileFormValues) => {
    setIsSubmitting(true);
    try {
      const includePassword = shouldShowPasswordField(
        isNewUser,
        inviteUsersViaEmail,
        isPlusEnabled,
        ssoEnabled,
        allowUsernameAndPassword,
        values.password_login_enabled,
      );

      const payload: UserCreateExtended = {
        username: values.username,
        email_address: values.email_address,
        first_name: values.first_name,
        last_name: values.last_name,
      };

      if (showPasswordLoginToggle) {
        payload.password_login_enabled = values.password_login_enabled;
      }

      if (includePassword && values.password) {
        payload.password = values.password;
      }

      const result = await onSubmit(payload);
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
        return;
      }
      message.success(
        isNewUser
          ? "User created. By default, new users are set to the Viewer role. To change the role, go to the Roles tab."
          : "User updated.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {contextHolder}
      {user?.has_invite && canReinvite && (
        <div className="mb-4">
          <Alert
            title={user.invite_expired ? "Invite expired" : "Invite pending"}
            description={
              user.invite_expired
                ? "This user's invitation has expired. Use the button to send a new invitation email."
                : "This user has not yet accepted their invitation. You can resend the invitation if needed."
            }
            type={user.invite_expired ? "warning" : "info"}
            showIcon
            action={
              <Button
                type="primary"
                onClick={handleReinviteClick}
                loading={isReinviting}
                size="small"
              >
                Reinvite
              </Button>
            }
          />
        </div>
      )}
      <Form
        form={form}
        layout="vertical"
        initialValues={formInitialValues}
        onFinish={handleSubmit}
        data-testid="user-profile-form"
      >
        <Flex justify="space-between" align="center" className="mb-4">
          <Text className="flex items-center text-sm font-semibold">
            Profile{" "}
            {user?.disabled && (
              <Tag
                color="success"
                className="ml-2"
                data-testid="invite-sent-badge"
              >
                Invite sent
              </Tag>
            )}
          </Text>
          {!isNewUser &&
            shouldShowPasswordManagement(
              isPlusEnabled,
              ssoEnabled,
              allowUsernameAndPassword,
              passwordLoginEnabled,
            ) && <PasswordManagement />}
        </Flex>

        <Form.Item
          name="username"
          label="Username"
          rules={isNewUser ? usernameRules : []}
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
            data-testid="input-email_address"
          />
        </Form.Item>
        <Form.Item name="first_name" label="First name">
          <Input
            placeholder="Enter first name of user"
            disabled={nameDisabled}
            data-testid="input-first_name"
          />
        </Form.Item>
        <Form.Item name="last_name" label="Last name">
          <Input
            placeholder="Enter last name of user"
            disabled={nameDisabled}
            data-testid="input-last_name"
          />
        </Form.Item>
        {showPasswordLoginToggle && (
          <Form.Item
            name="password_login_enabled"
            label="Allow password login"
            tooltip="When enabled, user can log in with username and password. When disabled, user must use SSO."
            valuePropName="checked"
          >
            <Switch
              disabled={!isNewUser}
              data-testid="input-password_login_enabled"
            />
          </Form.Item>
        )}
        {showPasswordField && (
          <Form.Item
            name="password"
            label="Password"
            tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
            rules={passwordRules}
          >
            <Input.Password data-testid="input-password" />
          </Form.Item>
        )}

        <Button
          htmlType="submit"
          type="primary"
          disabled={
            !form.isFieldsTouched() ||
            form.getFieldsError().some(({ errors }) => errors.length > 0)
          }
          loading={isSubmitting}
          data-testid="save-user-btn"
          className="mt-4"
        >
          Save
        </Button>
      </Form>
    </>
  );
};

export default UserProfileForm;
