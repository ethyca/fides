/**
 * RolesForm - RBAC-enabled role assignment form
 *
 * This component is used when the rbacManagement feature flag is enabled.
 * It displays roles from the database (including custom roles) and uses
 * the RBAC APIs for role assignment.
 */

import { useHasPermission } from "common/Restrict";
import {
  Button,
  Card,
  ChakraSpinner as Spinner,
  Checkbox,
  Flex,
  Typography,
  useChakraDisclosure as useDisclosure,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import React, { useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import {
  useAssignUserRoleMutation,
  useGetRolesQuery,
  useGetUserRolesQuery,
  useRemoveUserRoleMutation,
} from "~/features/rbac/rbac.slice";
import { ScopeRegistryEnum, System } from "~/types/api";

import AssignSystemsModal from "./AssignSystemsModal";
import { AssignSystemsDeleteTable } from "./AssignSystemsTable";
import {
  selectActiveUserId,
  selectActiveUsersManagedSystems,
  useGetUserManagedSystemsQuery,
  useUpdateUserManagedSystemsMutation,
} from "./user-management.slice";

const { Text, Title } = Typography;

// Role keys that cannot have systems assigned to them
const ROLES_WITHOUT_SYSTEM_ASSIGNMENT = [
  "approver",
  "respondent",
  "external_respondent",
];

const RolesForm = () => {
  const message = useMessage();
  const router = useRouter();
  const activeUserId = useAppSelector(selectActiveUserId);
  const assignSystemsModal = useDisclosure();

  // RBAC data fetching
  const { data: rbacRoles, isLoading: isLoadingRoles } = useGetRolesQuery({});
  const { data: userRbacRoles, isLoading: isLoadingUserRoles } =
    useGetUserRolesQuery(
      { userId: activeUserId ?? "" },
      { skip: !activeUserId },
    );

  const [assignUserRole] = useAssignUserRoleMutation();
  const [removeUserRole] = useRemoveUserRoleMutation();

  // System assignment data
  useGetUserManagedSystemsQuery(activeUserId as string, {
    skip: !activeUserId,
  });
  const initialManagedSystems = useAppSelector(selectActiveUsersManagedSystems);
  const [assignedSystems, setAssignedSystems] = useState<System[]>([]);
  const [updateUserManagedSystemsTrigger] =
    useUpdateUserManagedSystemsMutation();

  // Sync assigned systems when initial data loads
  useEffect(() => {
    setAssignedSystems(initialManagedSystems);
  }, [initialManagedSystems]);

  // Track selected roles locally for optimistic updates
  const [selectedRoleIds, setSelectedRoleIds] = useState<Set<string>>(
    new Set(),
  );
  const [isInitialized, setIsInitialized] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Initialize selected roles from user's current assignments
  const currentRoleIds = useMemo(() => {
    if (!userRbacRoles) return new Set<string>();
    return new Set(userRbacRoles.map((ur) => ur.role_id));
  }, [userRbacRoles]);

  // Initialize local state when data loads
  React.useEffect(() => {
    if (userRbacRoles && !isInitialized) {
      setSelectedRoleIds(currentRoleIds);
      setIsInitialized(true);
    }
  }, [userRbacRoles, currentRoleIds, isInitialized]);

  // Reset initialization when user changes
  React.useEffect(() => {
    setIsInitialized(false);
  }, [activeUserId]);

  // Get user's current role keys for permission checks
  const currentRoleKeys = useMemo(() => {
    if (!userRbacRoles || !rbacRoles) return [];
    return userRbacRoles
      .map((ur) => {
        const role = rbacRoles.find((r) => r.id === ur.role_id);
        return role?.key;
      })
      .filter((key): key is string => !!key);
  }, [userRbacRoles, rbacRoles]);

  const isLoading = isLoadingRoles || isLoadingUserRoles;

  // Check permissions
  const canAssignOwner = useHasPermission([
    ScopeRegistryEnum.USER_PERMISSION_ASSIGN_OWNERS,
  ]);

  const targetUserIsOwner = currentRoleKeys.includes("owner");
  const isExternalRespondent = currentRoleKeys.includes("external_respondent");

  // Check if selected roles support system assignment
  const selectedRolesAllowSystemAssignment = useMemo(() => {
    if (!rbacRoles || selectedRoleIds.size === 0) return false;
    // Check if any selected role allows system assignment
    for (const roleId of selectedRoleIds) {
      const role = rbacRoles.find((r) => r.id === roleId);
      if (role && !ROLES_WITHOUT_SYSTEM_ASSIGNMENT.includes(role.key)) {
        return true;
      }
    }
    return false;
  }, [rbacRoles, selectedRoleIds]);

  // Check if systems have changed
  const systemsHaveChanged = useMemo(() => {
    if (assignedSystems.length !== initialManagedSystems.length) return true;
    const initialKeys = new Set(initialManagedSystems.map((s) => s.fides_key));
    return assignedSystems.some((s) => !initialKeys.has(s.fides_key));
  }, [assignedSystems, initialManagedSystems]);

  // Check if there are unsaved changes
  const hasChanges = useMemo(() => {
    if (selectedRoleIds.size !== currentRoleIds.size) return true;
    for (const id of selectedRoleIds) {
      if (!currentRoleIds.has(id)) return true;
    }
    return systemsHaveChanged;
  }, [selectedRoleIds, currentRoleIds, systemsHaveChanged]);

  const handleRoleToggle = (roleId: string) => {
    setSelectedRoleIds((prev) => {
      const next = new Set(prev);
      if (next.has(roleId)) {
        next.delete(roleId);
      } else {
        next.add(roleId);
      }
      return next;
    });
  };

  const handleSave = async () => {
    if (!activeUserId || !userRbacRoles) return;

    setIsSaving(true);

    try {
      // Determine roles to add and remove
      const rolesToAdd = Array.from(selectedRoleIds).filter(
        (id) => !currentRoleIds.has(id),
      );
      const rolesToRemove = Array.from(currentRoleIds).filter(
        (id) => !selectedRoleIds.has(id),
      );

      // Remove roles
      for (const roleId of rolesToRemove) {
        const assignment = userRbacRoles.find((ur) => ur.role_id === roleId);
        if (assignment) {
          const result = await removeUserRole({
            userId: activeUserId,
            assignmentId: assignment.id,
          });
          if (isErrorResult(result)) {
            message.error(getErrorMessage(result.error));
            return;
          }
        }
      }

      // Add roles
      for (const roleId of rolesToAdd) {
        const result = await assignUserRole({
          userId: activeUserId,
          data: { role_id: roleId },
        });
        if (isErrorResult(result)) {
          message.error(getErrorMessage(result.error));
          return;
        }
      }

      // Save managed systems if the role supports it
      // Skip for roles that cannot have systems (like approver)
      if (selectedRolesAllowSystemAssignment) {
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

      message.success("Roles updated successfully");
    } finally {
      setIsSaving(false);
    }
  };

  if (!activeUserId) {
    return null;
  }

  if (isLoading) {
    return (
      <Flex justify="center" align="center" style={{ padding: 40 }}>
        <Spinner />
      </Flex>
    );
  }

  if (!canAssignOwner && targetUserIsOwner) {
    return (
      <Text data-testid="insufficient-access">
        You do not have sufficient access to change this user&apos;s roles.
      </Text>
    );
  }

  // Sort roles: system roles first (by priority), then custom roles alphabetically
  const sortedRoles = [...(rbacRoles || [])].sort((a, b) => {
    if (a.is_system_role && !b.is_system_role) return -1;
    if (!a.is_system_role && b.is_system_role) return 1;
    if (a.is_system_role && b.is_system_role) {
      return (b.priority || 0) - (a.priority || 0);
    }
    return a.name.localeCompare(b.name);
  });

  // Filter out inactive roles and external_respondent for regular users
  const availableRoles = sortedRoles.filter((role) => {
    if (!role.is_active) return false;
    if (isExternalRespondent) {
      return role.key === "external_respondent";
    }
    return role.key !== "external_respondent";
  });

  return (
    <Flex vertical gap={24}>
      <div>
        <Title level={5} style={{ marginBottom: 8 }}>
          Assign Roles
        </Title>
        <Text type="secondary">
          Select the roles for this user. Roles determine what actions the user
          can perform and what data they can access.
        </Text>
      </div>

      <Flex vertical gap={12}>
        {availableRoles.map((role) => {
          const isSelected = selectedRoleIds.has(role.id);
          const isOwnerRole = role.key === "owner";
          const isDisabled = isOwnerRole
            ? !canAssignOwner
            : isExternalRespondent;
          const supportsSystemAssignment =
            !ROLES_WITHOUT_SYSTEM_ASSIGNMENT.includes(role.key);

          return (
            <Card
              key={role.id}
              size="small"
              style={{
                cursor: isDisabled ? "not-allowed" : "pointer",
                opacity: isDisabled ? 0.6 : 1,
                borderColor: isSelected ? "#1890ff" : undefined,
                backgroundColor: isSelected ? "#e6f7ff" : undefined,
              }}
              onClick={() => !isDisabled && handleRoleToggle(role.id)}
            >
              <Flex vertical gap={12}>
                <Flex align="flex-start" gap={12}>
                  <Checkbox
                    checked={isSelected}
                    disabled={isDisabled}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!isDisabled) {
                        handleRoleToggle(role.id);
                      }
                    }}
                  />
                  <Flex vertical gap={4} style={{ flex: 1 }}>
                    <Flex align="center" gap={8}>
                      <Text strong>{role.name}</Text>
                      {role.is_system_role && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          System role
                        </Text>
                      )}
                      {!role.is_system_role && (
                        <Text
                          type="secondary"
                          style={{ fontSize: 12, color: "#52c41a" }}
                        >
                          Custom role
                        </Text>
                      )}
                    </Flex>
                    {role.description && (
                      <Text type="secondary" style={{ fontSize: 13 }}>
                        {role.description}
                      </Text>
                    )}
                  </Flex>
                </Flex>
                {/* Show system assignment section for selected roles that support it */}
                {isSelected && supportsSystemAssignment && (
                  <Flex
                    vertical
                    gap={12}
                    style={{ marginLeft: 32, marginTop: 8 }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Flex align="center" gap={4}>
                      <Text strong style={{ fontSize: 13 }}>
                        Assigned systems
                      </Text>
                      <InfoTooltip label="Assigned systems refer to those systems that have been specifically allocated to a user for management purposes. Users assigned to a system possess full edit permissions and are listed as the Data Steward for the respective system." />
                    </Flex>
                    <Button
                      type="primary"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        assignSystemsModal.onOpen();
                      }}
                      data-testid="assign-systems-btn"
                    >
                      Assign systems +
                    </Button>
                    <AssignSystemsDeleteTable
                      assignedSystems={assignedSystems}
                      onAssignedSystemChange={setAssignedSystems}
                    />
                  </Flex>
                )}
              </Flex>
            </Card>
          );
        })}
      </Flex>

      {/* System assignment modal */}
      {assignSystemsModal.isOpen && (
        <AssignSystemsModal
          isOpen={assignSystemsModal.isOpen}
          onClose={assignSystemsModal.onClose}
          assignedSystems={assignedSystems}
          onAssignedSystemChange={setAssignedSystems}
        />
      )}

      <Flex gap={12}>
        <Button onClick={() => router.push(USER_MANAGEMENT_ROUTE)}>
          Cancel
        </Button>
        <Button
          type="primary"
          onClick={handleSave}
          loading={isSaving}
          disabled={!hasChanges || isExternalRespondent}
          data-testid="save-btn"
        >
          Save
        </Button>
      </Flex>
    </Flex>
  );
};

export default RolesForm;
