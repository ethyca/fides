import {Box, Button, ButtonGroup, Flex, HStack, Stack, Text, useToast} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { useAPIHelper } from "common/hooks";
import { Form, Formik } from "formik";
import NextLink from "next/link";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { USER_MANAGEMENT_ROUTE } from "~/constants";
import { CustomTextInput } from "~/features/common/form/inputs";
import { passwordValidation } from "~/features/common/form/validation";
import { successToastParams } from "~/features/common/toast";

import PasswordManagement from "./PasswordManagement";
import { User, UserCreateResponse } from "./types";
import { selectActiveUserId, setActiveUserId } from "./user-management.slice";

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
  user: User;
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
  canChangePassword?: boolean;
}

const UserForm = ({
  user,
  onSubmit,
  initialValues,
  canEditNames,
  canChangePassword,
}: Props) => {
  const toast = useToast();
  const dispatch = useAppDispatch();

  const { handleError } = useAPIHelper();
  const activeUserId = useAppSelector(selectActiveUserId);

  const isNewUser = !activeUserId;
  const nameDisabled = isNewUser ? false : !canEditNames;

  const handleSubmit = async (values: FormValues) => {
    // first either update or create the user
    const result = await onSubmit(values);
    if ("error" in result) {
      handleError(result.error);
      return;
    }
    toast(successToastParams(`User ${isNewUser ? "created" : "updated"}`));
    dispatch(setActiveUserId(result.data.id));
  };
  const validationSchema = canChangePassword
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
                <Text display="flex" alignItems="center" fontSize="sm" fontWeight="semibold">
                  Profile
                </Text>
                <Box marginLeft="auto">
                  <PasswordManagement
                      user={user}
                  />
                </Box>
              </Flex>
              <CustomTextInput
                name="username"
                label="Username"
                variant="block"
                placeholder="Enter new username"
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
