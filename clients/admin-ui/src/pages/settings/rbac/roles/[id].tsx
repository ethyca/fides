import Layout from "common/Layout";
import {
  Alert,
  Button,
  Checkbox,
  Flex,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tag,
  Tooltip,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useEffect, useMemo, useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { RBAC_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useDeleteRoleMutation,
  useGetPermissionsQuery,
  useGetRoleByIdQuery,
  useGetRolesQuery,
  useUpdateRoleMutation,
  useUpdateRolePermissionsMutation,
} from "~/features/rbac";
import type { RBACPermission, RBACRole } from "~/types/api";

/**
 * Get all descendant role IDs for a given role.
 * Used to prevent inheritance cycles - a role cannot have one of its
 * descendants as a parent (which would create A -> B -> A cycles).
 */
const getDescendantRoleIds = (
  roleId: string,
  allRoles: RBACRole[],
): Set<string> => {
  const descendants = new Set<string>();

  const collectDescendants = (parentIds: string[]): void => {
    if (parentIds.length === 0) {
      return;
    }

    const children = allRoles.filter(
      (r) => r.parent_role_id && parentIds.includes(r.parent_role_id),
    );
    const newChildIds = children
      .map((c) => c.id)
      .filter((id) => !descendants.has(id));

    newChildIds.forEach((id) => descendants.add(id));

    if (newChildIds.length > 0) {
      collectDescendants(newChildIds);
    }
  };

  collectDescendants([roleId]);
  return descendants;
};

// Scopes that are seeded in the database but have no corresponding endpoint.
// These are hidden from the UI to avoid confusion.
// See: fidesplus RBAC_SYSTEM.md documentation for details.
const HIDDEN_UNUSED_SCOPES = [
  "rbac_user_role:update", // No PUT endpoint for user role assignments
  "rbac_constraint:update", // No PUT endpoint for constraints
];

const RoleDetailPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const message = useMessage();
  const modal = useModal();
  const [form] = Form.useForm();

  const {
    data: role,
    isLoading,
    error,
  } = useGetRoleByIdQuery(id as string, {
    skip: !id,
  });
  const {
    data: allRoles,
    isLoading: isRolesLoading,
    error: rolesError,
  } = useGetRolesQuery({});
  const {
    data: permissions,
    isLoading: isPermissionsLoading,
    error: permissionsError,
  } = useGetPermissionsQuery({});
  const [updateRole, { isLoading: isUpdating }] = useUpdateRoleMutation();
  const [updatePermissions, { isLoading: isUpdatingPermissions }] =
    useUpdateRolePermissionsMutation();
  const [deleteRole, { isLoading: isDeleting }] = useDeleteRoleMutation();

  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);

  // Initialize form and selected permissions when role data loads
  useEffect(() => {
    if (role) {
      form.setFieldsValue({
        name: role.name,
        description: role.description,
        parent_role_id: role.parent_role_id,
        priority: role.priority,
        is_active: role.is_active,
      });
      setSelectedPermissions(role.permissions);
    }
  }, [role, form]);

  // Group permissions by resource type
  const groupedPermissions = useMemo(() => {
    if (!permissions) {
      return {};
    }
    return permissions
      .filter((perm) => !HIDDEN_UNUSED_SCOPES.includes(perm.code))
      .reduce<Record<string, RBACPermission[]>>((acc, perm) => {
        const resourceType = perm.resource_type || "general";
        if (!acc[resourceType]) {
          // eslint-disable-next-line no-param-reassign
          acc[resourceType] = [];
        }
        acc[resourceType].push(perm);
        return acc;
      }, {});
  }, [permissions]);

  // Filter out current role and its descendants from parent options
  // to prevent inheritance cycles (A -> B -> A)
  const parentRoleOptions = useMemo(() => {
    if (!allRoles || !id) {
      return [];
    }
    const descendantIds = getDescendantRoleIds(id as string, allRoles);
    return allRoles
      .filter((r) => r.id !== id && !descendantIds.has(r.id))
      .map((r) => ({
        label: `${r.name} (${r.key})`,
        value: r.id,
      }));
  }, [allRoles, id]);

  const handleSave = async () => {
    if (!id) {
      return;
    }
    try {
      const values = await form.validateFields();
      await Promise.all([
        updateRole({ roleId: id as string, data: values }).unwrap(),
        updatePermissions({
          roleId: id as string,
          data: { permission_codes: selectedPermissions },
        }).unwrap(),
      ]);
      message.success("Role saved successfully");
    } catch (err) {
      message.error("Failed to save role");
    }
  };

  const togglePermission = (code: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(code) ? prev.filter((p) => p !== code) : [...prev, code],
    );
  };

  const handleDeleteRole = async () => {
    if (!id || !role) {
      return;
    }
    try {
      await deleteRole(id as string).unwrap();
      message.success(`Role "${role.name}" deleted successfully`);
      router.push(RBAC_ROUTE);
    } catch (err) {
      message.error("Failed to delete role");
    }
  };

  const confirmDelete = () => {
    if (!role) {
      return;
    }
    modal.confirm({
      title: "Delete role",
      content: (
        <Typography.Text>
          Are you sure you want to delete &quot;{role.name}&quot;? This action
          cannot be undone.
        </Typography.Text>
      ),
      okText: "Delete",
      okButtonProps: { danger: true },
      centered: true,
      icon: null,
      onOk: () => handleDeleteRole(),
      className: "delete-role-confirmation-modal",
    });
  };

  if (error || rolesError || permissionsError) {
    return (
      <ErrorPage
        error={(error ?? rolesError ?? permissionsError)!}
        defaultMessage="A problem occurred while fetching RBAC data"
      />
    );
  }

  if (isLoading || isRolesLoading || isPermissionsLoading || !role) {
    return (
      <Layout title="Edit role">
        <Flex justify="center" align="center" style={{ minHeight: 400 }}>
          <Spin />
        </Flex>
      </Layout>
    );
  }

  const permissionColumns = [
    {
      title: "Permission",
      dataIndex: "code",
      key: "code",
      render: (code: string) => <code>{code}</code>,
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
    },
    {
      title: "Assigned",
      key: "assigned",
      render: (_: unknown, record: RBACPermission) => {
        const isInherited = role.inherited_permissions.includes(record.code);
        const isSelected = selectedPermissions.includes(record.code);
        return (
          <Space>
            <Checkbox
              checked={isSelected || isInherited}
              disabled={role.is_system_role || isInherited}
              onChange={() => togglePermission(record.code)}
            />
            {isInherited && <Tag color="minos">Inherited</Tag>}
          </Space>
        );
      },
    },
  ];

  return (
    <Layout title={`Edit Role: ${role.name}`}>
      <PageHeader
        heading={role.name}
        isSticky={false}
        className="pb-0"
        breadcrumbItems={[
          { title: "Role management", href: RBAC_ROUTE },
          { title: role.name },
        ]}
        rightContent={
          <Space>
            {!role.is_system_role && (
              <Button
                type="primary"
                onClick={handleSave}
                loading={isUpdating || isUpdatingPermissions}
              >
                Save
              </Button>
            )}
            <Tooltip
              title={
                role.is_system_role
                  ? "System roles cannot be deleted"
                  : undefined
              }
            >
              <Button
                danger
                disabled={role.is_system_role}
                onClick={() => confirmDelete()}
                loading={isDeleting}
              >
                Delete
              </Button>
            </Tooltip>
          </Space>
        }
      />

      <Flex vertical gap="large">
        <div>
          <Flex align="center" gap={8} className="mb-4">
            <Typography.Title level={4} className="m-0">
              Role details
            </Typography.Title>
            <Space>
              <Tag color={role.is_system_role ? "info" : "nectar"}>
                {role.is_system_role ? "System" : "Custom"}
              </Tag>
              <Tag color={role.is_active ? "success" : "default"}>
                {role.is_active ? "Active" : "Inactive"}
              </Tag>
            </Space>
          </Flex>
          <Form form={form} layout="vertical" disabled={role.is_system_role}>
            <Form.Item
              name="name"
              label="Name"
              rules={[{ required: true, message: "Name is required" }]}
            >
              <Input />
            </Form.Item>
            <Form.Item name="description" label="Description">
              <Input.TextArea rows={3} />
            </Form.Item>
            <Form.Item name="parent_role_id" label="Parent role">
              <Select
                aria-label="Parent role"
                allowClear
                placeholder="Select parent role for inheritance"
                options={parentRoleOptions}
              />
            </Form.Item>
            <Form.Item name="priority" label="Priority">
              <InputNumber aria-label="Priority" min={0} max={100} />
            </Form.Item>
            <Form.Item name="is_active" label="Active" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Form>
        </div>

        <div>
          <Typography.Title level={4}>Permissions</Typography.Title>
          {role.is_system_role && (
            <Typography.Text type="secondary" className="mb-4 block">
              System role permissions cannot be modified.
            </Typography.Text>
          )}
          {Object.entries(groupedPermissions).map(([resourceType, perms]) => (
            <div key={resourceType} className="mb-6">
              <Typography.Title level={5} className="capitalize">
                {resourceType.replace(/_/g, " ")}
              </Typography.Title>
              {resourceType === "system" && (
                <Alert
                  message="System permissions apply globally"
                  description="System permissions (system:create, system:read, system:update, system:delete) grant access to ALL systems in the organization. Use system_manager permissions for per-system access control."
                  type="warning"
                  showIcon
                  className="mb-4"
                />
              )}
              {resourceType === "rbac_role" && (
                <Alert
                  message="Role management grants full permission control"
                  description="Users with rbac_role:update can assign any permission to roles, including permissions they don't personally have. Only grant role management permissions to trusted administrators."
                  type="warning"
                  showIcon
                  className="mb-4"
                />
              )}
              <Table
                dataSource={perms}
                columns={permissionColumns}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </div>
          ))}
        </div>
      </Flex>
    </Layout>
  );
};

export default RoleDetailPage;
