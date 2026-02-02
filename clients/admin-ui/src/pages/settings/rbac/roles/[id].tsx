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
  Switch,
  Table,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useEffect, useMemo, useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { RBAC_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useGetPermissionsQuery,
  useGetRoleByIdQuery,
  useGetRolesQuery,
  useUpdateRoleMutation,
  useUpdateRolePermissionsMutation,
} from "~/features/rbac";
import type { RBACPermission, RBACRoleUpdate } from "~/types/api";

const RoleDetailPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const message = useMessage();
  const [form] = Form.useForm();

  const {
    data: role,
    isLoading,
    error,
  } = useGetRoleByIdQuery(id as string, {
    skip: !id,
  });
  const { data: allRoles } = useGetRolesQuery({});
  const { data: permissions } = useGetPermissionsQuery({});
  const [updateRole, { isLoading: isUpdating }] = useUpdateRoleMutation();
  const [updatePermissions, { isLoading: isUpdatingPermissions }] =
    useUpdateRolePermissionsMutation();

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
    return permissions.reduce<Record<string, RBACPermission[]>>((acc, perm) => {
      const resourceType = perm.resource_type || "general";
      const result = { ...acc };
      if (!result[resourceType]) {
        result[resourceType] = [];
      }
      result[resourceType].push(perm);
      return result;
    }, {});
  }, [permissions]);

  // Filter out current role and system roles from parent options
  const parentRoleOptions = useMemo(() => {
    if (!allRoles) {
      return [];
    }
    return allRoles
      .filter((r) => r.id !== id)
      .map((r) => ({
        label: `${r.name} (${r.key})`,
        value: r.id,
      }));
  }, [allRoles, id]);

  const handleSubmit = async (values: RBACRoleUpdate) => {
    if (!id) {
      return;
    }
    try {
      await updateRole({ roleId: id as string, data: values }).unwrap();
      message.success("Role updated successfully");
    } catch (err) {
      message.error("Failed to update role");
    }
  };

  const handleSavePermissions = async () => {
    if (!id) {
      return;
    }
    try {
      await updatePermissions({
        roleId: id as string,
        data: { permission_codes: selectedPermissions },
      }).unwrap();
      message.success("Permissions updated successfully");
    } catch (err) {
      message.error("Failed to update permissions");
    }
  };

  const togglePermission = (code: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(code) ? prev.filter((p) => p !== code) : [...prev, code],
    );
  };

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching the role"
      />
    );
  }

  if (isLoading || !role) {
    return (
      <Layout title="Loading...">
        <Flex justify="center" align="center" style={{ minHeight: 400 }}>
          Loading...
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
      <PageHeader heading={role.name} isSticky={false} className="pb-0">
        <Space>
          <Tag color={role.is_system_role ? "info" : "success"}>
            {role.is_system_role ? "System Role" : "Custom Role"}
          </Tag>
          <Tag color={role.is_active ? "success" : "default"}>
            {role.is_active ? "Active" : "Inactive"}
          </Tag>
        </Space>
      </PageHeader>

      <Flex vertical gap={24} className="p-6">
        {/* Role Details Form */}
        <div className="rounded-lg border border-gray-200 p-6">
          <Typography.Title level={4}>Role Details</Typography.Title>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            disabled={role.is_system_role}
          >
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
            <Form.Item name="parent_role_id" label="Parent Role">
              <Select
                aria-label="Parent Role"
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
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={isUpdating}>
                  Save Changes
                </Button>
                <Button onClick={() => router.push(RBAC_ROUTE)}>Cancel</Button>
              </Space>
            </Form.Item>
          </Form>
        </div>

        {/* Permissions Section */}
        <div className="rounded-lg border border-gray-200 p-6">
          <Flex justify="space-between" align="center" className="mb-4">
            <Typography.Title level={4} className="m-0">
              Permissions
            </Typography.Title>
            {!role.is_system_role && (
              <Button
                type="primary"
                onClick={handleSavePermissions}
                loading={isUpdatingPermissions}
              >
                Save Permissions
              </Button>
            )}
          </Flex>
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
                  description="Note: system:read permission currently grants access to ALL systems in the organization, regardless of any resource scoping. Fine-grained per-system access control is not yet implemented."
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
