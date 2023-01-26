import {
  Box,
  Button,
  Checkbox,
  Divider,
  Heading,
  Stack,
  Text,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { useAPIHelper } from "common/hooks";
import { Form, Formik } from "formik";
import NextLink from "next/link";
import { useRouter } from "next/router";
import * as Yup from "yup";

import { USER_MANAGEMENT_ROUTE, USER_PRIVILEGES } from "~/constants";
import { CustomTextInput } from "~/features/common/form/inputs";
import { passwordValidation } from "~/features/common/form/validation";

import PasswordManagement from "./PasswordManagement";
import { User, UserCreateResponse } from "./types";
import { useUpdateUserPermissionsMutation } from "./user-management.slice";

const defaultInitialValues = {
  username: "",
  first_name: "",
  last_name: "",
  password: "",
  scopes: ["privacy-request:read"],
};

export type FormValues = typeof defaultInitialValues;

const ValidationSchema = Yup.object().shape({
  username: Yup.string().required().label("Username"),
  first_name: Yup.string().label("First name"),
  last_name: Yup.string().label("Last name"),
  password: passwordValidation.label("Password"),
  scopes: Yup.array().of(Yup.string()),
});

interface Props {
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
  onSubmit,
  initialValues,
  canEditNames,
  canChangePassword,
}: Props) => {
  const router = useRouter();
  const { handleError } = useAPIHelper();
  const profileId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : router.query.id;
  const isNewUser = profileId == null;
  const nameDisabled = isNewUser ? false : !canEditNames;
  const [updateUserPermissions] = useUpdateUserPermissionsMutation();

  const handleSubmit = async (values: FormValues) => {
    // first either update or create the user
    const result = await onSubmit(values);
    if ("error" in result) {
      handleError(result.error);
      return;
    }

    // then issue a separate call to update their permissions
    const { data } = result;
    const userWithPrivileges = {
      user_id: data.id,
      scopes: [...new Set([...values.scopes, "privacy-request:read"])],
    };
    const updateUserPermissionsResult = await updateUserPermissions(
      userWithPrivileges
    );
    if (!("error" in updateUserPermissionsResult)) {
      router.push(USER_MANAGEMENT_ROUTE);
    }
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
      {({ values, setFieldValue }) => (
        <Form>
          <Box maxW={["xs", "xs", "100%"]} width="100%">
            <Stack mb={8} spacing={6}>
              <Stack mb={8} spacing={6} maxWidth="40%">
                <CustomTextInput
                  name="username"
                  label="Username"
                  placeholder="Enter new username"
                />
                <CustomTextInput
                  name="first_name"
                  label="First Name"
                  placeholder="Enter first name of user"
                  disabled={nameDisabled}
                />
                <CustomTextInput
                  name="last_name"
                  label="Last Name"
                  placeholder="Enter last name of user"
                  disabled={nameDisabled}
                />
                <PasswordManagement profileId={profileId} />
              </Stack>
              <Divider mb={7} mt={7} />
              <Heading fontSize="xl" colorScheme="primary">
                Privileges
              </Heading>
              <Text>Select privileges to assign to this user</Text>
              <Divider mb={2} mt={2} />

              <Stack spacing={[1, 5]} direction="column">
                {USER_PRIVILEGES.map((policy) => {
                  const isChecked = values.scopes.indexOf(policy.scope) >= 0;
                  return (
                    <Checkbox
                      colorScheme="purple"
                      key={policy.privilege}
                      onChange={() => {
                        if (!isChecked) {
                          setFieldValue(`scopes`, [
                            ...values.scopes,
                            policy.scope,
                          ]);
                        } else {
                          setFieldValue(
                            "scopes",
                            values.scopes.filter(
                              (scope) => scope !== policy.scope
                            )
                          );
                        }
                      }}
                      id={`scopes-${policy.privilege}`}
                      name="scopes"
                      isChecked={isChecked}
                      value={
                        policy.scope === "privacy-request:read"
                          ? undefined
                          : policy.scope
                      }
                      isDisabled={policy.scope === "privacy-request:read"}
                      isReadOnly={policy.scope === "privacy-request:read"}
                    >
                      {policy.privilege}
                    </Checkbox>
                  );
                })}
              </Stack>
            </Stack>
            <NextLink href={USER_MANAGEMENT_ROUTE} passHref>
              <Button variant="outline" mr={3} size="sm">
                Cancel
              </Button>
            </NextLink>
            <Button
              type="submit"
              bg="primary.800"
              _hover={{ bg: "primary.400" }}
              _active={{ bg: "primary.500" }}
              colorScheme="primary"
              size="sm"
            >
              Save
            </Button>
          </Box>
        </Form>
      )}
    </Formik>
  );
};

export default UserForm;
