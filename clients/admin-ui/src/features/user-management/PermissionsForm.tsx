import { useHasPermission } from "common/Restrict";
import {
  AntButton as Button,
  AntTooltip as Tooltip,
  Flex,
  Spinner,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import React, { useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { ROLES } from "~/features/user-management/constants";
import { RoleRegistryEnum, ScopeRegistryEnum, System } from "~/types/api";

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
  const router = useRouter();
  const activeUserId = useAppSelector(selectActiveUserId);
  useGetUserManagedSystemsQuery(activeUserId as string, {
    skip: !activeUserId,
  });
  const {
    isOpen: chooseApproverIsOpen,
    onOpen: chooseApproverOpen,
    onClose: chooseApproverClose,
  } = useDisclosure();
  const initialManagedSystems = useAppSelector(selectActiveUsersManagedSystems);
  const [assignedSystems, setAssignedSystems] = useState<System[]>(
    initialManagedSystems,
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
    },
  );

  const [updateUserPermissionMutationTrigger] =
    useUpdateUserPermissionsMutation();

  // Check if the current user is an external respondent
  const isExternalRespondent = Boolean(
    userPermissions?.roles?.includes(RoleRegistryEnum.EXTERNAL_RESPONDENT),
  );

  const updatePermissions = async (values: FormValues) => {
    if (chooseApproverIsOpen) {
      chooseApproverClose();
    }
    if (!activeUserId) {
      return;
    }

    // Unassigning systems from an approver happens automatically on BE when the role is saved.
    // If we attempt to assign systems to the approver role, the BE will throw an error,
    // so we skip calling the endpoint.
    const skipAssigningSystems = values.roles.includes(
      RoleRegistryEnum.APPROVER,
    );

    const userPermissionsResult = await updateUserPermissionMutationTrigger({
      user_id: activeUserId,
      payload: { roles: values.roles },
    });

    if (isErrorResult(userPermissionsResult)) {
      toast(errorToastParams(getErrorMessage(userPermissionsResult.error)));
      return;
    }
    if (!skipAssigningSystems) {
      const fidesKeys = assignedSystems.map((s) => s.fides_key);
      const userSystemsResult = await updateUserManagedSystemsTrigger({
        userId: activeUserId,
        fidesKeys,
      });
      if (isErrorResult(userSystemsResult)) {
        toast(errorToastParams(getErrorMessage(userSystemsResult.error)));
        return;
      }
    }
    toast(successToastParams("Permissions updated"));
  };

  const handleSubmit = async (values: FormValues) => {
    if (!activeUserId) {
      return;
    }
    if (
      assignedSystems.length > 0 &&
      values.roles.includes(RoleRegistryEnum.APPROVER)
    ) {
      // approvers cannot be system managers on back-end
      chooseApproverOpen();
    } else {
      await updatePermissions(values);
    }
  };

  // This prevents logged-in users with contributor role from being able to assign owner roles
  const canAssignOwner = useHasPermission([
    ScopeRegistryEnum.USER_PERMISSION_ASSIGN_OWNERS,
  ]);

  if (!activeUserId) {
    return null;
  }

  if (isLoading) {
    return <Spinner />;
  }

  if (
    !canAssignOwner &&
    userPermissions?.roles?.includes(RoleRegistryEnum.OWNER)
  ) {
    return (
      <Text data-testid="insufficient-access">
        You do not have sufficient access to change this user&apos;s
        permissions.
      </Text>
    );
  }

  const initialValues = userPermissions?.roles
    ? { roles: userPermissions.roles }
    : defaultInitialValues;

  // Filter roles based on whether the user is external respondent
  const availableRoles = ROLES.filter((role) => {
    // For external respondents, only show their current role
    if (isExternalRespondent) {
      return role.roleKey === RoleRegistryEnum.EXTERNAL_RESPONDENT;
    }
    // For regular users, exclude external respondent role
    return role.roleKey !== RoleRegistryEnum.EXTERNAL_RESPONDENT;
  });

  const externalRespondentTooltip =
    "To invite a new External respondent user, create a manual task integration and then click on the 'Manage secure access' button";

  const saveButtonTooltip = isExternalRespondent
    ? "External respondent role cannot be changed"
    : undefined;

  return (
    <Formik
      onSubmit={handleSubmit}
      initialValues={initialValues}
      enableReinitialize
    >
      {({ values, isSubmitting, dirty }) => (
        <Form>
          <Stack spacing={7}>
            <Stack spacing={3} data-testid="role-options">
              <Flex alignItems="center">
                <Text fontSize="sm" fontWeight="semibold" mr={1}>
                  User role
                </Text>
                <InfoTooltip label="A user's role in the organization determines what parts of the UI they can access and which functions are available to them." />
              </Flex>
              {availableRoles.map((role) => {
                const isSelected = values.roles.indexOf(role.roleKey) >= 0;
                const isOwnerRole = role.roleKey === RoleRegistryEnum.OWNER;
                const isRoleDisabled = isOwnerRole
                  ? !canAssignOwner
                  : isExternalRespondent;

                return (
                  <RoleOption
                    key={role.roleKey}
                    isSelected={isSelected}
                    isDisabled={isRoleDisabled}
                    assignedSystems={assignedSystems}
                    onAssignedSystemChange={setAssignedSystems}
                    {...role}
                  />
                );
              })}
              {/* Show disabled external respondent option for regular users */}
              {!isExternalRespondent && (
                <Tooltip title={externalRespondentTooltip}>
                  <Button
                    disabled
                    data-testid="role-option-External respondent"
                  >
                    External respondent
                  </Button>
                </Tooltip>
              )}
            </Stack>
            <div>
              <Button onClick={() => router.push(USER_MANAGEMENT_ROUTE)}>
                Cancel
              </Button>
              <Tooltip title={saveButtonTooltip}>
                <Button
                  className="ml-2"
                  type="primary"
                  htmlType="submit"
                  loading={isSubmitting}
                  disabled={
                    (!dirty && assignedSystems === initialManagedSystems) ||
                    isExternalRespondent
                  }
                  data-testid="save-btn"
                >
                  Save
                </Button>
              </Tooltip>
            </div>
          </Stack>
          <ConfirmationModal
            isOpen={chooseApproverIsOpen}
            onClose={chooseApproverClose}
            onConfirm={() => updatePermissions(values)}
            title="Change role to Approver"
            testId="downgrade-to-approver-confirmation-modal"
            continueButtonText="Yes"
            message={
              <Text>
                Switching to an approver role will remove all assigned systems.
                Do you wish to proceed?
              </Text>
            }
          />
        </Form>
      )}
    </Formik>
  );
};

export default PermissionsForm;
