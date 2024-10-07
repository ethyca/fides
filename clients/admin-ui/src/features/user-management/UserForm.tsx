import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  AntButton,
  Badge,
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
import { useFlags } from "~/features/common/features";
import { CustomTextInput } from "~/features/common/form/inputs";
import { passwordValidation } from "~/features/common/form/validation";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { TrashCanSolidIcon } from "~/features/common/Icon/TrashCanSolidIcon";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useGetEmailInviteStatusQuery } from "~/features/messaging/messaging.slice";
import { useGetAllOpenIDProvidersQuery } from "~/features/openid-authentication/openprovider.slice";

import PasswordManagement from "./PasswordManagement";
import { User, UserCreate, UserCreateResponse } from "./types";
import { selectActiveUser, setActiveUserId } from "./user-management.slice";

const defaultInitialValues: UserCreate = {
  username: "",
  first_name: "",
  email_address: "",
  last_name: "",
  password: "",
};

export type FormValues = typeof defaultInitialValues;

const ValidationSchema = Yup.object().shape({
  username: Yup.string().required().label("Username"),
  email_address: Yup.string().email().required().label("Email address"),
  first_name: Yup.string().label("First name"),
  last_name: Yup.string().label("Last name"),
  password: passwordValidation.label("Password"),
});

export interface Props {
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

const UserForm = ({ onSubmit, initialValues, canEditNames }: Props) => {
  const router = useRouter();
  const toast = useToast();
  const dispatch = useAppDispatch();
  const deleteModal = useDisclosure();

  const activeUser = useAppSelector(selectActiveUser);
  const { data: emailInviteStatus } = useGetEmailInviteStatusQuery();
  const inviteUsersViaEmail = emailInviteStatus?.enabled;
  const { flags } = useFlags();

  const isNewUser = !activeUser;
  const nameDisabled = isNewUser ? false : !canEditNames;
  const showPasswordField = isNewUser && !inviteUsersViaEmail;

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

  const { data: openidProviders } = useGetAllOpenIDProvidersQuery();

  const passwordFieldIsRequired =
    !flags.ssoAuthentication || !openidProviders?.length;

  if (!passwordFieldIsRequired) {
    validationSchema = ValidationSchema.shape({
      password: passwordValidation.optional().label("Password"),
    });
  }

  validationSchema = showPasswordField
    ? validationSchema
    : validationSchema.omit(["password"]);

  return (
    <Formik
      onSubmit={handleSubmit}
      initialValues={initialValues ?? defaultInitialValues}
      validationSchema={validationSchema}
    >
      {({ dirty, isSubmitting, isValid }) => (
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
                    <Badge
                      bg="green.500"
                      color="white"
                      paddingLeft="2"
                      marginLeft="2"
                      textTransform="none"
                      paddingRight="8px"
                      height="18px"
                      lineHeight="18px"
                      borderRadius="6px"
                      fontWeight="500"
                      textAlign="center"
                      data-testid="invite-sent-badge"
                    >
                      Invite sent
                    </Badge>
                  )}
                </Text>
                <Box marginLeft="auto">
                  <HStack>
                    <PasswordManagement />
                    {!isNewUser ? (
                      <Box>
                        <AntButton
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
              />
              <CustomTextInput
                name="email_address"
                label="Email address"
                variant="block"
                placeholder="Enter email of user"
                isRequired
              />
              <CustomTextInput
                name="first_name"
                label="First Name"
                variant="block"
                placeholder="Enter first name of user"
                disabled={nameDisabled}
              />
              <CustomTextInput
                name="last_name"
                label="Last Name"
                variant="block"
                placeholder="Enter last name of user"
                disabled={nameDisabled}
              />
              {showPasswordField ? (
                <CustomTextInput
                  name="password"
                  label="Password"
                  variant="block"
                  placeholder="********"
                  type="password"
                  tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
                  isRequired={passwordFieldIsRequired}
                />
              ) : null}
            </Stack>
            <div>
              <AntButton
                onClick={() => router.push(USER_MANAGEMENT_ROUTE)}
                className="mr-3"
              >
                Cancel
              </AntButton>
              <AntButton
                htmlType="submit"
                type="primary"
                disabled={!dirty || !isValid}
                loading={isSubmitting}
                data-testid="save-user-btn"
              >
                Save
              </AntButton>
            </div>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default UserForm;
