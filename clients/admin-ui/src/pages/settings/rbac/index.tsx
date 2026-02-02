import Layout from "common/Layout";
import { Button, Flex, Space, Table, Tag, Typography, useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { RBAC_ROLE_NEW_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetRolesQuery, useDeleteRoleMutation } from "~/features/rbac";
import type { RBACRole } from "~/types/api";

const RBAC_COPY =
  "Role-based access control (RBAC) allows you to create custom roles with specific permissions. " +
  "Assign roles to users to control their access to resources and actions within the system.";

const RBACPage: NextPage = () => {
  const router = useRouter();
  const message = useMessage();
  const { data: roles, isLoading, error } = useGetRolesQuery({ include_inactive: true });
  const [deleteRole, { isLoading: isDeleting }] = useDeleteRoleMutation();

  const handleDeleteRole = async (role: RBACRole) => {
    if (role.is_system_role) {
      message.error("System roles cannot be deleted");
      return;
    }
    try {
      await deleteRole(role.id).unwrap();
      message.success(`Role "${role.name}" deleted successfully`);
    } catch (err) {
      message.error("Failed to delete role");
    }
  };

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching roles"
      />
    );
  }

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string, record: RBACRole) => (
        <a onClick={() => router.push(`/settings/rbac/roles/${record.id}`)}>
          {name}
        </a>
      ),
    },
    {
      title: "Key",
      dataIndex: "key",
      key: "key",
      render: (key: string) => <code>{key}</code>,
    },
    {
      title: "Type",
      key: "type",
      render: (_: unknown, record: RBACRole) => (
        <Tag color={record.is_system_role ? "info" : "success"}>
          {record.is_system_role ? "System" : "Custom"}
        </Tag>
      ),
    },
    {
      title: "Permissions",
      key: "permissions",
      render: (_: unknown, record: RBACRole) => {
        const directCount = record.permissions.length;
        const inheritedCount = record.inherited_permissions.length;
        return (
          <Space>
            <Tag>{directCount} direct</Tag>
            {inheritedCount > 0 && <Tag color="minos">{inheritedCount} inherited</Tag>}
          </Space>
        );
      },
    },
    {
      title: "Status",
      key: "status",
      render: (_: unknown, record: RBACRole) => (
        <Tag color={record.is_active ? "success" : "default"}>
          {record.is_active ? "Active" : "Inactive"}
        </Tag>
      ),
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: RBACRole) => (
        <Space>
          <Button
            size="small"
            onClick={() => router.push(`/settings/rbac/roles/${record.id}`)}
          >
            Edit
          </Button>
          {!record.is_system_role && (
            <Button
              size="small"
              danger
              onClick={() => handleDeleteRole(record)}
              loading={isDeleting}
            >
              Delete
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Layout title="Role Management">
      <PageHeader heading="Role Management" isSticky={false} className="pb-0">
        <Typography.Paragraph className="max-w-screen-md">
          {RBAC_COPY}
        </Typography.Paragraph>
      </PageHeader>
      <Flex vertical gap={16} className="p-6">
        <Flex justify="flex-end">
          <Button type="primary" onClick={() => router.push(RBAC_ROLE_NEW_ROUTE)}>
            Create Custom Role
          </Button>
        </Flex>
        <Table
          dataSource={roles || []}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={false}
        />
      </Flex>
    </Layout>
  );
};

export default RBACPage;
