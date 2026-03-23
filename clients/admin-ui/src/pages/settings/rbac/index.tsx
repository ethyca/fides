import Layout from "common/Layout";
import {
  Button,
  Flex,
  Space,
  Table,
  Tag,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { RBAC_ROLE_NEW_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useDeleteRoleMutation, useGetRolesQuery } from "~/features/rbac";
import type { RBACRole } from "~/types/api";

const RBACPage: NextPage = () => {
  const router = useRouter();
  const message = useMessage();
  const modal = useModal();
  const {
    data: roles,
    isLoading,
    error,
  } = useGetRolesQuery({ include_inactive: true });
  const [deleteRole, { isLoading: isDeleting }] = useDeleteRoleMutation();
  const [deletingRoleId, setDeletingRoleId] = useState<string | null>(null);

  const handleDeleteRole = async (role: RBACRole) => {
    if (role.is_system_role) {
      message.error("System roles cannot be deleted");
      return;
    }
    setDeletingRoleId(role.id);
    try {
      await deleteRole(role.id).unwrap();
      message.success(`Role "${role.name}" deleted successfully`);
    } catch (err) {
      message.error("Failed to delete role");
    }
    setDeletingRoleId(null);
  };

  const confirmDelete = (role: RBACRole) => {
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
      onOk: () => handleDeleteRole(role),
      className: "delete-role-confirmation-modal",
    });
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
        <LinkCell href={`/settings/rbac/roles/${record.id}`}>{name}</LinkCell>
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
            <Tag>{directCount} Direct</Tag>
            {inheritedCount > 0 && (
              <Tag color="minos">{inheritedCount} Inherited</Tag>
            )}
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
              onClick={() => confirmDelete(record)}
              loading={isDeleting && deletingRoleId === record.id}
            >
              Delete
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Layout title="Role management">
      <PageHeader
        heading="Role management"
        isSticky={false}
        className="pb-0"
        rightContent={
          <Button
            type="primary"
            onClick={() => router.push(RBAC_ROLE_NEW_ROUTE)}
          >
            Create role
          </Button>
        }
      >
        <Typography.Paragraph className="max-w-screen-sm">
          Create and manage roles to define fine-grained access control. Assign
          roles to users to control what resources and actions they can access
          within the system.
        </Typography.Paragraph>
      </PageHeader>
      <Flex vertical gap={16}>
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
