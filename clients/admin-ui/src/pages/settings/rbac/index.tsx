import Layout from "common/Layout";
import {
  Button,
  Flex,
  Space,
  Table,
  Tag,
  Typography,
  useChakraDisclosure as useDisclosure,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { RBAC_ROLE_NEW_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useDeleteRoleMutation, useGetRolesQuery } from "~/features/rbac";
import type { RBACRole } from "~/types/api";

const RBAC_COPY =
  "Role-based access control (RBAC) allows you to create custom roles with specific permissions. " +
  "Assign roles to users to control their access to resources and actions within the system.";

const RBACPage: NextPage = () => {
  const router = useRouter();
  const message = useMessage();
  const {
    data: roles,
    isLoading,
    error,
  } = useGetRolesQuery({ include_inactive: true });
  const [deleteRole, { isLoading: isDeleting }] = useDeleteRoleMutation();
  const [roleToDelete, setRoleToDelete] = useState<RBACRole | null>(null);
  const {
    isOpen: isDeleteModalOpen,
    onOpen: openDeleteModal,
    onClose: closeDeleteModal,
  } = useDisclosure();

  const handleDeleteRole = async () => {
    if (!roleToDelete) {
      return;
    }
    if (roleToDelete.is_system_role) {
      message.error("System roles cannot be deleted");
      closeDeleteModal();
      return;
    }
    try {
      await deleteRole(roleToDelete.id).unwrap();
      message.success(`Role "${roleToDelete.name}" deleted successfully`);
    } catch (err) {
      message.error("Failed to delete role");
    }
    closeDeleteModal();
    setRoleToDelete(null);
  };

  const confirmDelete = (role: RBACRole) => {
    setRoleToDelete(role);
    openDeleteModal();
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
        <Button
          type="link"
          onClick={() => router.push(`/settings/rbac/roles/${record.id}`)}
          className="p-0"
        >
          {name}
        </Button>
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
            {inheritedCount > 0 && (
              <Tag color="minos">{inheritedCount} inherited</Tag>
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
              loading={isDeleting && roleToDelete?.id === record.id}
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
          <Button
            type="primary"
            onClick={() => router.push(RBAC_ROLE_NEW_ROUTE)}
          >
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
      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          closeDeleteModal();
          setRoleToDelete(null);
        }}
        onConfirm={handleDeleteRole}
        title="Delete Role"
        message={
          <Typography.Text>
            Are you sure you want to delete &quot;{roleToDelete?.name}&quot;?
            This action cannot be undone.
          </Typography.Text>
        }
        continueButtonText="Delete"
        testId="delete-role-confirmation-modal"
      />
    </Layout>
  );
};

export default RBACPage;
