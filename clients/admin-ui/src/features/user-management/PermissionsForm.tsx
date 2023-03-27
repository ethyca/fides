import {
  Button,
  ButtonGroup,
  Flex,
  Spinner,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import { useHasRole } from "common/Restrict";
import { Form, Formik } from "formik";
import NextLink from "next/link";
import { useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { USER_MANAGEMENT_ROUTE } from "~/constants";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { ROLES } from "~/features/user-management/constants";
import { RoleRegistryEnum, System } from "~/types/api";

import RoleOption from "./RoleOption";
import {
  selectActiveUserId,
  selectActiveUsersManagedSystems,
  useGetUserManagedSystemsQuery,
  useGetUserPermissionsQuery,
  useUpdateUserManagedSystemsMutation,
  useUpdateUserPermissionsMutation,
} from "./user-management.slice";

const defaultInitialValues = {
  roles: [] as RoleRegistryEnum[],
};

export type FormValues = typeof defaultInitialValues;

const PermissionsForm = () => {
  const toast = useToast();
  const activeUserId = useAppSelector(selectActiveUserId);
  useGetUserManagedSystemsQuery(activeUserId as string, {
    skip: !activeUserId,
  });
  const initialManagedSystems = useAppSelector(selectActiveUsersManagedSystems);
  const [assignedSystems, setAssignedSystems] = useState<System[]>(
    initialManagedSystems
  );
  const [updateUserManagedSystemsTrigger] =
    useUpdateUserManagedSystemsMutation();

  useEffect(() => {
    setAssignedSystems(initialManagedSystems);
  }, [initialManagedSystems]);

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
    const userPermissionsResult = await updateUserPermissionMutationTrigger({
      user_id: activeUserId,
      // Scopes are not editable in the UI, but make sure we retain whatever scopes
      // the user might've already had
      payload: { scopes: userPermissions?.scopes, roles: values.roles },
    });

    if (isErrorResult(userPermissionsResult)) {
      toast(errorToastParams(getErrorMessage(userPermissionsResult.error)));
      return;
    }
    const fidesKeys = assignedSystems.map((s) => s.fides_key);
    const userSystemsResult = await updateUserManagedSystemsTrigger({
      userId: activeUserId,
      fidesKeys,
    });
    if (isErrorResult(userSystemsResult)) {
      toast(errorToastParams(getErrorMessage(userSystemsResult.error)));
      return;
    }
    toast(successToastParams("Permissions updated"));
  };

  // This prevents logged-in users with contributor role from being able to assign owner roles
  const isOwner = useHasRole([RoleRegistryEnum.OWNER]);

  if (!activeUserId) {
    return null;
  }

  if (isLoading) {
    return <Spinner />;
  }

  if (!isOwner && userPermissions?.roles?.includes(RoleRegistryEnum.OWNER)) {
    return (
      <Text>
        You do not have sufficient access to change this user&apos;s
        permissions.
      </Text>
    );
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
                    isDisabled={
                      role.roleKey === RoleRegistryEnum.OWNER ? !isOwner : false
                    }
                    assignedSystems={assignedSystems}
                    onAssignedSystemChange={setAssignedSystems}
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
                disabled={!dirty && assignedSystems === initialManagedSystems}
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
