import Layout from "common/Layout";
import { Button, Flex, Space, Table, Tag, Typography } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import React from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { RBAC_ROLE_NEW_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useGetRolesQuery } from "~/features/rbac";
import type { RBACRole } from "~/types/api";

const RBACPage: NextPage = () => {
  const {
    data: roles,
    isLoading,
    error,
  } = useGetRolesQuery({ include_inactive: true });

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
        <Tag color={record.is_system_role ? "default" : "nectar"}>
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
            <Tag color="corinth">{directCount} Direct</Tag>
            {inheritedCount > 0 && (
              <Tag color="default">{inheritedCount} Inherited</Tag>
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
  ];

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Role management"
          description="Create and manage roles to define fine-grained access control. Assign roles to users to control what resources and actions they can access within the system."
        />
        <SidePanel.Actions>
          <NextLink href={RBAC_ROLE_NEW_ROUTE} passHref>
            <Button type="primary">Create role</Button>
          </NextLink>
        </SidePanel.Actions>
      </SidePanel>
      <Layout title="Role management">
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
    </>
  );
};

export default RBACPage;
