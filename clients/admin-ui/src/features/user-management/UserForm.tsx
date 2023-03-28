import {
  Box,
  Button,
  ButtonGroup,
  Flex,
  HStack,
  IconButton,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { useAPIHelper } from "common/hooks";
import { Form, Formik } from "formik";
import NextLink from "next/link";
import React from "react";
import DeleteUserModal from "user-management/DeleteUserModal";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { USER_MANAGEMENT_ROUTE } from "~/constants";
import { CustomTextInput } from "~/features/common/form/inputs";
import { passwordValidation } from "~/features/common/form/validation";
import { TrashCanSolidIcon } from "~/features/common/Icon/TrashCanSolidIcon";
import { successToastParams } from "~/features/common/toast";

import PasswordManagement from "./PasswordManagement";
import { User } from "./types";
import { selectActiveUser, setActiveUserId } from "./user-management.slice";

const defaultInitialValues = {
  username: "",
  first_name: "",
  last_name: "",
  password: "",
};

export type FormValues = typeof defaultInitialValues;

const ValidationSchema = Yup.object().shape({
  username: Yup.string().required().label("Username"),
  first_name: Yup.string().label("First name"),
  last_name: Yup.string().label("Last name"),
  password: passwordValidation.label("Password"),
});

export interface Props {
  onSubmit: (values: FormValues) => Promise<
    | void
    | {
        data: User;
      }
    | {
        error: FetchBaseQueryError | SerializedError;
      }
  >;
  initialValues?: FormValues;
  canEditNames?: boolean;
}

const UserForm = ({ onSubmit, initialValues, canEditNames }: Props) => {
  const toast = useToast();
  const dispatch = useAppDispatch();
  const deleteModal = useDisclosure();

  const { handleError } = useAPIHelper();

  const activeUser = useAppSelector(selectActiveUser);

  const isNewUser = !activeUser;
  const nameDisabled = isNewUser ? false : !canEditNames;

  const handleSubmit = async (values: FormValues) => {
    // first either update or create the user
    const result = await onSubmit(values);
    if (result && "error" in result) {
      handleError(result.error);
      return;
    }
    toast(successToastParams(`User ${isNewUser ? "created" : "updated"}`));
    if (result && result.data) {
      dispatch(setActiveUserId(result.data.id));
    }
  };

  // The password field is only available when creating a new user.
  // Otherwise, it is within the UpdatePasswordModal
  const validationSchema = isNewUser
    ? ValidationSchema
    : ValidationSchema.omit(["password"]);

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
                  Profile
                </Text>
                <Box marginLeft="auto">
                  <HStack>
                    <PasswordManagement />
                    {!isNewUser ? (
                      <Box>
                        <IconButton
                          aria-label="delete"
                          icon={<TrashCanSolidIcon />}
                          variant="outline"
                          size="sm"
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
              {!activeUser ? (
                <CustomTextInput
                  name="password"
                  label="Password"
                  variant="block"
                  placeholder="********"
                  type="password"
                  tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
                  isRequired
                />
              ) : null}
            </Stack>
            <ButtonGroup size="sm">
              <NextLink href={USER_MANAGEMENT_ROUTE} passHref>
                <Button variant="outline" mr={3}>
                  Cancel
                </Button>
              </NextLink>
              <Button
                type="submit"
                bg="primary.800"
                _hover={{ bg: "primary.400" }}
                _active={{ bg: "primary.500" }}
                colorScheme="primary"
                disabled={!dirty || !isValid}
                isLoading={isSubmitting}
                data-testid="save-user-btn"
              >
                Save
              </Button>
            </ButtonGroup>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default UserForm;
