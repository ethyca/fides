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
import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomTextInput } from "~/features/common/form/inputs";
import { passwordValidation } from "~/features/common/form/validation";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { TrashCanSolidIcon } from "~/features/common/Icon/TrashCanSolidIcon";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { selectPlusSecuritySettings } from "~/features/config-settings/config-settings.slice";
import { useGetEmailInviteStatusQuery } from "~/features/messaging/messaging.slice";
import { useGetAllOpenIDProvidersQuery } from "~/features/openid-authentication/openprovider.slice";

import PasswordManagement from "./PasswordManagement";
import { User, UserCreate, UserCreateResponse } from "./types";
import {
  isPasswordFieldRequired,
  shouldShowLoginMethodSelector,
  shouldShowPasswordField,
  shouldShowPasswordManagement,
} from "./user-form-helpers";
import { selectActiveUser, setActiveUserId } from "./user-management.slice";

// Extended type for the form that includes login_method
interface UserCreateExtended extends UserCreate {
  login_method?: string;
}

const defaultInitialValues: UserCreateExtended = {
  username: "",
  first_name: "",
  email_address: "",
  last_name: "",
  password: "",
  login_method: "sso",
};

export type FormValues = typeof defaultInitialValues;

const ValidationSchema = Yup.object().shape({
  username: Yup.string().required().label("Username"),
  email_address: Yup.string().email().required().label("Email address"),
  first_name: Yup.string().label("First name"),
  last_name: Yup.string().label("Last name"),
  password: passwordValidation.label("Password"),
  login_method: Yup.string().label("Login method"),
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
  const router = useRouter();
  const toast = useToast();
  const dispatch = useAppDispatch();
  const deleteModal = useDisclosure();

  const activeUser = useAppSelector(selectActiveUser);
  const { data: emailInviteStatus } = useGetEmailInviteStatusQuery();
  const inviteUsersViaEmail = emailInviteStatus?.enabled || false;
  const { plus: isPlusEnabled } = useFeatures();
  const plusSecuritySettings = useAppSelector(selectPlusSecuritySettings);
  const allowUsernameAndPassword =
    plusSecuritySettings?.allow_username_password_fallback;

  const isNewUser = !activeUser;
  const nameDisabled = isNewUser ? false : !canEditNames;

  const { data: openidProviders } = useGetAllOpenIDProvidersQuery();
  const ssoEnabled = (openidProviders && openidProviders.length > 0) || false;

  const showPasswordField = shouldShowPasswordField(
    isNewUser,
    inviteUsersViaEmail,
    isPlusEnabled,
    ssoEnabled,
    allowUsernameAndPassword || false,
    activeUser?.login_method,
  );

  const showLoginMethodSelector = shouldShowLoginMethodSelector(
    isPlusEnabled,
    ssoEnabled,
    allowUsernameAndPassword,
  );

  const passwordFieldIsRequired = isPasswordFieldRequired(
    isNewUser,
    inviteUsersViaEmail,
    isPlusEnabled,
    ssoEnabled,
    allowUsernameAndPassword || false,
    activeUser?.login_method,
  );

  const handleSubmit = async (values: FormValues) => {
    // first either update or create the user
    const { password, ...payloadWithoutPassword } = values;
    const payload = showPasswordField ? values : payloadWithoutPassword;
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

  // The password field is only available when creating a new user.
  // Otherwise, it is within the UpdatePasswordModal
  let validationSchema: Yup.ObjectSchema<Yup.AnyObject> = ValidationSchema;

  validationSchema = showPasswordField
    ? validationSchema
    : validationSchema.omit(["password"]);

  validationSchema = showLoginMethodSelector
    ? validationSchema
    : validationSchema.omit(["login_method"]);

  return (
    <Formik
      onSubmit={handleSubmit}
      initialValues={initialValues ?? defaultInitialValues}
      validationSchema={validationSchema}
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
                      activeUser?.login_method,
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
              {showLoginMethodSelector && (
                <ControlledSelect
                  name="login_method"
                  label="Login method"
                  layout="stacked"
                  defaultValue="sso"
                  options={[
                    {
                      label: "Username and Password",
                      value: "username_password",
                    },
                    { label: "SSO", value: "sso" },
                  ]}
                  isRequired
                  data-testid="select-login-method"
                />
              )}
              {shouldShowPasswordField(
                isNewUser,
                inviteUsersViaEmail,
                isPlusEnabled,
                ssoEnabled,
                allowUsernameAndPassword || false,
                values?.login_method,
              ) && (
                <CustomTextInput
                  name="password"
                  label="Password"
                  variant="block"
                  placeholder="********"
                  type="password"
                  tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
                  isRequired={passwordFieldIsRequired}
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
