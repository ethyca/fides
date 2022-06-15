// @ts-nocheck
import {
  Button,
  chakra,
  Checkbox,
  Divider,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import { useFormik } from "formik";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React from "react";
import { useSelector } from "react-redux";

import { USER_PRIVILEGES } from "../../constants";
import { selectUser } from "../auth";
import { User } from "./types";
import UpdatePasswordModal from "./UpdatePasswordModal";
import {
  useEditUserMutation,
  useGetUserByIdQuery,
  useGetUserPermissionsQuery,
  useUpdateUserPermissionsMutation,
} from "./user-management.slice";

const useUserForm = () => {
  const router = useRouter();
  const { id: profileId } = router.query;
  const currentUser: User = useSelector(selectUser) ?? {};
  const [updateUserPermissions] = useUpdateUserPermissionsMutation();
  const [editUser] = useEditUserMutation(profileId);
  const { data: existingUser } = useGetUserByIdQuery(profileId);
  const { data: existingScopes } = useGetUserPermissionsQuery(profileId);
  const toast = useToast();

  const formik = useFormik({
    initialValues: {
      username: existingUser?.username ?? "",
      first_name: existingUser?.first_name ?? "",
      last_name: existingUser?.last_name ?? "",
      password: existingUser?.password ?? "",
      scopes: existingScopes?.scopes ?? "",
      id: existingUser?.id ?? "",
    },
    enableReinitialize: true,
    onSubmit: async (values) => {
      const userBody = {
        username: values.username ? values.username : existingUser?.username,
        first_name: values.first_name
          ? values.first_name
          : existingUser?.first_name,
        last_name: values.last_name
          ? values.last_name
          : existingUser?.last_name,
        password: values.password ? values.password : existingUser?.password,
        id: existingUser?.id,
      };

      const { error: editUserError, data } = await editUser(userBody);

      if (editUserError) {
        toast({
          status: "error",
          description: editUserError.data.detail.length
            ? `${editUserError.data.detail[0].msg}`
            : "An unexpected error occurred. Please try again.",
        });
        return;
      }

      if (editUserError && editUserError.status === 422) {
        toast({
          status: "error",
          description: editUserError.data.detail.length
            ? `${editUserError.data.detail[0].msg}`
            : "An unexpected error occurred. Please try again.",
        });
      }

      const userWithPrivileges = {
        id: data ? data.id : null,
        scopes: [...new Set(values.scopes, "privacy-request:read")],
      };

      const { error: updatePermissionsError } = await updateUserPermissions(
        userWithPrivileges
      );

      if (!updatePermissionsError) {
        router.push("/user-management");
      }
    },
    validate: () => {
      const errors: {
        username?: string;
        first_name?: string;
        last_name?: string;
        password?: string;
      } = {};

      return errors;
    },
  });

  let canUpdateUser = false;
  const { data: userPermissions = { scopes: [] } } = useGetUserPermissionsQuery(
    currentUser.id
  );
  canUpdateUser = userPermissions.scopes.includes("user:update");

  return {
    ...formik,
    existingScopes,
    existingUser,
    profileId,
    isOwnProfile: profileId === currentUser.id,
    canUpdateUser,
  };
};

const EditUserForm: React.FC = () => {
  const {
    dirty,
    existingUser,
    profileId,
    isOwnProfile,
    handleBlur,
    handleChange,
    handleSubmit,
    isValid,
    setFieldValue,
    canUpdateUser,
    values,
  } = useUserForm();

  return (
    <div>
      <main>
        <Heading mb={4} fontSize="xl" colorScheme="primary">
          Profile
        </Heading>
        <Divider mb={7} />
        <chakra.form
          onSubmit={handleSubmit}
          maxW={["xs", "xs", "100%"]}
          width="100%"
        >
          <Stack mb={8} spacing={6}>
            <FormControl id="username">
              <FormLabel htmlFor="username" fontWeight="medium">
                Username
              </FormLabel>
              <Input
                id="username"
                maxWidth="40%"
                name="username"
                focusBorderColor="primary.500"
                placeholder={existingUser?.username}
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.username}
                isReadOnly
                isDisabled
              />
            </FormControl>

            <FormControl id="first_name">
              <FormLabel htmlFor="first_name" fontWeight="medium">
                First Name
              </FormLabel>
              <Input
                id="first_name"
                maxWidth="40%"
                name="first_name"
                focusBorderColor="primary.500"
                placeholder={existingUser?.first_name}
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.first_name}
                isReadOnly={!canUpdateUser}
                isDisabled={!canUpdateUser}
              />
            </FormControl>

            <FormControl id="last_name">
              <FormLabel htmlFor="last_name" fontWeight="medium">
                Last Name
              </FormLabel>
              <Input
                id="last_name"
                maxWidth="40%"
                name="last_name"
                focusBorderColor="primary.500"
                placeholder={existingUser?.last_name}
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.last_name}
                isReadOnly={!canUpdateUser}
                isDisabled={!canUpdateUser}
              />
            </FormControl>

            {/* Only the owner of this profile can change their password */}
            {isOwnProfile ? <UpdatePasswordModal id={profileId} /> : null}

            <Divider mb={7} mt={7} />

            <Heading fontSize="xl" colorScheme="primary">
              Privileges
            </Heading>
            <Text>Edit privileges assigned to this user</Text>
            <Divider mb={2} mt={2} />

            <Stack spacing={[1, 5]} direction="column">
              {USER_PRIVILEGES.map((policy) => {
                const isChecked = values.scopes
                  ? values.scopes.indexOf(policy.scope) >= 0
                  : false;
                return (
                  <Checkbox
                    colorScheme="purple"
                    isChecked={isChecked}
                    key={`${policy.privilege}`}
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
                    value={policy.scope}
                    isDisabled={policy.scope === "privacy-request:read"}
                    isReadOnly={policy.scope === "privacy-request:read"}
                  >
                    {policy.privilege}
                  </Checkbox>
                );
              })}
            </Stack>
          </Stack>

          <NextLink href="/user-management" passHref>
            <Button mr={3} variant="outline" size="sm">
              Cancel
            </Button>
          </NextLink>
          <Button
            type="submit"
            bg="primary.800"
            _hover={{ bg: "primary.400" }}
            _active={{ bg: "primary.500" }}
            colorScheme="primary"
            disabled={!existingUser && !(isValid && dirty)}
            size="sm"
          >
            Save
          </Button>
        </chakra.form>
      </main>
    </div>
  );
};

export default EditUserForm;
