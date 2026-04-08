import Layout from "common/Layout";
import {
  Button,
  Flex,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useMemo } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RBAC_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import { useCreateRoleMutation, useGetRolesQuery } from "~/features/rbac";
import type { RBACRoleCreate } from "~/types/api";
import type { RTKErrorResult } from "~/types/errors/api";

const NewRolePage: NextPage = () => {
  const router = useRouter();
  const message = useMessage();
  const [form] = Form.useForm();

  const { data: allRoles } = useGetRolesQuery({});
  const [createRole, { isLoading }] = useCreateRoleMutation();

  // Build parent role options - all roles including system roles can be parents
  const parentRoleOptions = useMemo(() => {
    if (!allRoles) {
      return [];
    }
    return allRoles.map((r) => ({
      label: `${r.name} (${r.key})`,
      value: r.id,
    }));
  }, [allRoles]);

  const handleSubmit = async (values: RBACRoleCreate) => {
    try {
      const newRole = await createRole(values).unwrap();
      message.success(`Role "${newRole.name}" created successfully`);
      router.push(`/settings/rbac/roles/${newRole.id}`);
    } catch (err: unknown) {
      message.error(getErrorMessage(err as RTKErrorResult["error"]));
    }
  };

  // Auto-generate key from name
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.value;
    const key = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_|_$/g, "");
    form.setFieldValue("key", key);
  };

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Create role"
          breadcrumbItems={[
            { title: "Role management", href: RBAC_ROUTE },
            { title: "Create role" },
          ]}
        />
      </SidePanel>
      <Layout title="Create role">

      <Flex vertical>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ priority: 0 }}
          className="max-w-2xl"
        >
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: "Name is required" }]}
          >
            <Input
              placeholder="e.g., Privacy Analyst"
              onChange={handleNameChange}
            />
          </Form.Item>

          <Form.Item
            name="key"
            label="Key"
            rules={[
              {
                pattern: /^[a-z][a-z0-9_]*$/,
                message:
                  "Key must start with a letter and contain only lowercase letters, numbers, and underscores",
              },
            ]}
            tooltip="Auto-generated from name. Used as a machine-readable identifier."
          >
            <Input placeholder="e.g., privacy_analyst" />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <Input.TextArea
              rows={3}
              placeholder="Describe what this role is used for..."
            />
          </Form.Item>

          <Form.Item
            name="parent_role_id"
            label="Parent role"
            tooltip="Optionally inherit permissions from another role."
          >
            <Select
              aria-label="Parent role"
              allowClear
              placeholder="Select a parent role"
              options={parentRoleOptions}
            />
          </Form.Item>

          <Form.Item
            name="priority"
            label="Priority"
            tooltip="Higher priority roles take precedence when permissions conflict (0–100)."
          >
            <InputNumber
              aria-label="Priority"
              min={0}
              max={100}
              style={{ width: "100%" }}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={isLoading}>
                Create role
              </Button>
              <NextLink href={RBAC_ROUTE} passHref>
                <Button>Cancel</Button>
              </NextLink>
            </Space>
          </Form.Item>
        </Form>
      </Flex>
      </Layout>
    </>
  );
};

export default NewRolePage;
