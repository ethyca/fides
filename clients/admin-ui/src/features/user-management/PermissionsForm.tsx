import { useHasPermission } from "common/Restrict";
import { Button, Flex, Spin, Tooltip, Typography, useMessage } from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import React, { useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
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

/**
 * Legacy permissions form for non-RBAC mode.
 *
 * When RBAC is enabled (alphaRbac flag), UserManagementTabs renders RolesForm
 * instead of this component. This component only handles legacy permissions.
 */
const { Text } = Typography;

const PermissionsForm = () => {
  const message = useMessage();
  const router = useRouter();

  const activeUserId = useAppSelector(selectActiveUserId);
  useGetUserManagedSystemsQuery(activeUserId as string, {
    skip: !activeUserId,
  });
  const [isChooseApproverOpen, setIsChooseApproverOpen] = useState(false);
  const initialManagedSystems = useAppSelector(selectActiveUsersManagedSystems);
  const [assignedSystems, setAssignedSystems] = useState<System[]>(
    initialManagedSystems,
  );
  const [updateUserManagedSystemsTrigger] =
    useUpdateUserManagedSystemsMutation();

  useEffect(() => {
    setAssignedSystems(initialManagedSystems);
  }, [initialManagedSystems]);

  // Legacy permission hooks
  const { data: userPermissions, isLoading } = useGetUserPermissionsQuery(
    activeUserId ?? "",
    {
      skip: !activeUserId,
    },
  );

  const [updateUserPermissionMutationTrigger] =
    useUpdateUserPermissionsMutation();

  // Check if the current user is an external respondent
  const isExternalRespondent = useMemo(() => {
    return Boolean(
      userPermissions?.roles?.includes(RoleRegistryEnum.EXTERNAL_RESPONDENT),
    );
  }, [userPermissions?.roles]);

  const initialValues = useMemo(() => {
    return userPermissions?.roles
      ? { roles: userPermissions.roles }
      : defaultInitialValues;
  }, [userPermissions?.roles]);

  // Check if target user is an owner
  const targetUserIsOwner = useMemo(() => {
    return userPermissions?.roles?.includes(RoleRegistryEnum.OWNER);
  }, [userPermissions?.roles]);

  const updatePermissionsLegacy = async (values: FormValues) => {
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
      message.error(getErrorMessage(userPermissionsResult.error));
      return;
    }
    if (!skipAssigningSystems) {
      const fidesKeys = assignedSystems.map((s) => s.fides_key);
      const userSystemsResult = await updateUserManagedSystemsTrigger({
        userId: activeUserId,
        fidesKeys,
      });
      if (isErrorResult(userSystemsResult)) {
        message.error(getErrorMessage(userSystemsResult.error));
        return;
      }
    }
    message.success("Permissions updated");
  };

  const updatePermissions = async (values: FormValues) => {
    if (isChooseApproverOpen) {
      setIsChooseApproverOpen(false);
    }
    if (!activeUserId) {
      return;
    }

    await updatePermissionsLegacy(values);
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
      setIsChooseApproverOpen(true);
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
    return <Spin />;
  }

  if (!canAssignOwner && targetUserIsOwner) {
    return (
      <Text data-testid="insufficient-access">
        You do not have sufficient access to change this user&apos;s
        permissions.
      </Text>
    );
  }

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
          <Flex vertical gap={28}>
            <Flex vertical gap={12} data-testid="role-options">
              <Flex align="center">
                <Text className="mr-1 text-sm font-semibold">User role</Text>
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
            </Flex>
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
          </Flex>
          <ConfirmationModal
            isOpen={isChooseApproverOpen}
            onClose={() => setIsChooseApproverOpen(false)}
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
