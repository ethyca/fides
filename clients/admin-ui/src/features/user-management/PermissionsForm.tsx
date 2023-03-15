import {
  Button,
  ButtonGroup,
  Flex,
  Spinner,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import NextLink from "next/link";

import { useAppSelector } from "~/app/hooks";
import { USER_MANAGEMENT_ROUTE } from "~/constants";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { RoleRegistryEnum } from "~/types/api";
import { ROLES } from "~/types/api/models/RolesDataMapping";

import QuestionTooltip from "../common/QuestionTooltip";
import RoleOption from "./RoleOption";
import {
  selectActiveUserId,
  useGetUserPermissionsQuery,
  useUpdateUserPermissionsMutation,
} from "./user-management.slice";

const defaultInitialValues = {
  roles: [] as RoleRegistryEnum[],
};

export type FormValues = typeof defaultInitialValues;

const PermissionsForm = () => {
  const toast = useToast();
  const activeUserId = useAppSelector(selectActiveUserId);

  const { data: userPermissions, isLoading } = useGetUserPermissionsQuery(
    activeUserId ?? "",
    {
      skip: !activeUserId,
    }
  );

  const [updateUserPermissionMutationTrigger] =
    useUpdateUserPermissionsMutation();

  const handleSubmit = async (values: FormValues) => {
    if (!activeUserId) {
      return;
    }
    const result = await updateUserPermissionMutationTrigger({
      user_id: activeUserId,
      // Scopes are not editable in the UI, but make sure we retain whatever scopes
      // the user might've already had
      payload: { scopes: userPermissions?.scopes, roles: values.roles },
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }
    toast(successToastParams("Permissions updated"));
  };

  if (!activeUserId) {
    return null;
  }

  if (isLoading) {
    return <Spinner />;
  }

  const initialValues = userPermissions?.roles
    ? { roles: userPermissions.roles }
    : defaultInitialValues;

  return (
    <Formik
      onSubmit={handleSubmit}
      initialValues={initialValues}
      enableReinitialize
    >
      {({ values, isSubmitting, dirty }) => (
        <Form>
          <Stack spacing={7}>
            <Stack spacing={3}>
              <Flex alignItems="center">
                <Text fontSize="sm" fontWeight="semibold" mr={1}>
                  User role
                </Text>
                <QuestionTooltip label="A user's role in the organization determines what parts of the UI they can access and which functions are available to them." />
              </Flex>
              {ROLES.map((role) => {
                const isSelected = values.roles.indexOf(role.roleKey) >= 0;
                return (
                  <RoleOption
                    key={role.roleKey}
                    isSelected={isSelected}
                    {...role}
                  />
                );
              })}
            </Stack>
            <ButtonGroup size="sm">
              <NextLink href={USER_MANAGEMENT_ROUTE} passHref>
                <Button variant="outline">Cancel</Button>
              </NextLink>
              <Button
                colorScheme="primary"
                type="submit"
                isLoading={isSubmitting}
                disabled={!dirty}
                data-testid="save-btn"
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

export default PermissionsForm;
