import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  AntButton as Button,
  AntTag as Tag,
  Box,
  Flex,
  HStack,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import React from "react";
import DeleteUserModal from "user-management/DeleteUserModal";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { CustomSwitch, CustomTextInput } from "~/features/common/form/inputs";
import { passwordValidation } from "~/features/common/form/validation";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { TrashCanSolidIcon } from "~/features/common/Icon/TrashCanSolidIcon";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  selectPlusSecuritySettings,
  useGetConfigurationSettingsQuery,
} from "~/features/config-settings/config-settings.slice";
import { useGetEmailInviteStatusQuery } from "~/features/messaging/messaging.slice";
import { useGetAllOpenIDProvidersQuery } from "~/features/openid-authentication/openprovider.slice";

import PasswordManagement from "./PasswordManagement";
import { User, UserCreate, UserCreateResponse } from "./types";
import {
  shouldShowPasswordField,
  shouldShowPasswordLoginToggle,
  shouldShowPasswordManagement,
} from "./user-form-helpers";
import { selectActiveUser, setActiveUserId } from "./user-management.slice";

// Extended type for the form with password_login_enabled
interface UserCreateExtended extends UserCreate {
  password_login_enabled?: boolean;
}

const defaultInitialValues: UserCreateExtended = {
  username: "",
  first_name: "",
  email_address: "",
  last_name: "",
  password: "",
  password_login_enabled: false,
};

export type FormValues = typeof defaultInitialValues;

const ValidationSchema = Yup.object().shape({
  username: Yup.string().required().label("Username"),
  email_address: Yup.string().email().required().label("Email address"),
  first_name: Yup.string().label("First name"),
  last_name: Yup.string().label("Last name"),
  password: passwordValidation.label("Password"),
  password_login_enabled: Yup.boolean().label("Allow password login"),
});

export interface UserFormProps {
  onSubmit: (values: FormValues) => Promise<
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
  const toast = useToast();
  const dispatch = useAppDispatch();
  const deleteModal = useDisclosure();

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

  const handleSubmit = async (values: FormValues) => {
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
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }
    toast(
      successToastParams(
        `${
          isNewUser
            ? "User created. By default, new users are set to the Viewer role. To change the role, please go to the Permissions tab."
            : "User updated."
        }`,
      ),
    );
    if (result?.data) {
      dispatch(setActiveUserId(result.data.id));
    }
  };

  return (
    <Formik
      onSubmit={handleSubmit}
      initialValues={formInitialValues}
      validationSchema={ValidationSchema}
      data-testid="user-form"
    >
      {({ dirty, isSubmitting, isValid, values }) => (
        <Form>
          <Stack maxW={["xs", "xs", "100%"]} width="100%" spacing={7}>
            <Stack spacing={6} maxWidth="55%">
              <Flex>
                <Text
                  display="flex"
                  alignItems="center"
                  fontSize="sm"
                  fontWeight="semibold"
                >
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
                <Box marginLeft="auto">
                  <HStack>
                    {shouldShowPasswordManagement(
                      isPlusEnabled,
                      ssoEnabled,
                      allowUsernameAndPassword || false,
                      values.password_login_enabled,
                    ) && (
                      <PasswordManagement data-testid="password-management" />
                    )}
                    {!isNewUser ? (
                      <Box>
                        <Button
                          aria-label="delete"
                          icon={<TrashCanSolidIcon />}
                          onClick={deleteModal.onOpen}
                          data-testid="delete-user-btn"
                        />
                        <DeleteUserModal user={activeUser} {...deleteModal} />
                      </Box>
                    ) : null}
                  </HStack>
                </Box>
              </Flex>
              <CustomTextInput
                name="username"
                label="Username"
                variant="block"
                placeholder="Enter new username"
                disabled={!isNewUser}
                isRequired
                data-testid="input-username"
              />
              <CustomTextInput
                name="email_address"
                label="Email address"
                variant="block"
                placeholder="Enter email of user"
                isRequired
                data-testid="input-email-address"
              />
              <CustomTextInput
                name="first_name"
                label="First name"
                variant="block"
                placeholder="Enter first name of user"
                disabled={nameDisabled}
                data-testid="input-first-name"
              />
              <CustomTextInput
                name="last_name"
                label="Last name"
                variant="block"
                placeholder="Enter last name of user"
                disabled={nameDisabled}
                data-testid="input-last-name"
              />
              {showPasswordLoginToggle && (
                <CustomSwitch
                  name="password_login_enabled"
                  label="Allow password login"
                  tooltip="When enabled, user can log in with username and password. When disabled, user must use SSO."
                  variant="stacked"
                  isDisabled={!isNewUser}
                  data-testid="toggle-allow-password-login"
                  size="default"
                />
              )}
              {shouldShowPasswordField(
                isNewUser,
                inviteUsersViaEmail,
                isPlusEnabled,
                ssoEnabled,
                allowUsernameAndPassword,
                values.password_login_enabled,
              ) && (
                <CustomTextInput
                  name="password"
                  label="Password"
                  variant="block"
                  placeholder="********"
                  type="password"
                  tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
                  isRequired
                  data-testid="input-password"
                />
              )}
            </Stack>
            <div>
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
                disabled={!dirty || !isValid}
                loading={isSubmitting}
                data-testid="save-user-btn"
              >
                Save
              </Button>
            </div>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default UserForm;
