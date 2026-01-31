import Layout from "common/Layout";
import {
  Button,
  Flex,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Typography,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useMemo } from "react";

import { RBAC_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useCreateRoleMutation, useGetRolesQuery } from "~/features/rbac";
import type { RBACRoleCreate } from "~/types/api";

const NewRolePage: NextPage = () => {
  const router = useRouter();
  const message = useMessage();
  const [form] = Form.useForm();

  const { data: allRoles } = useGetRolesQuery({});
  const [createRole, { isLoading }] = useCreateRoleMutation();

  // Filter out system roles from parent options
  const parentRoleOptions = useMemo(() => {
    if (!allRoles) return [];
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
      const errorMessage =
        err && typeof err === "object" && "data" in err
          ? (err as { data?: { detail?: string } }).data?.detail
          : "Failed to create role";
      message.error(errorMessage || "Failed to create role");
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
    <Layout title="Create Custom Role">
      <PageHeader heading="Create Custom Role" isSticky={false} className="pb-0">
        <Typography.Paragraph className="max-w-screen-md">
          Create a new custom role with specific permissions. You can optionally
          inherit permissions from a parent role.
        </Typography.Paragraph>
      </PageHeader>

      <Flex vertical className="p-6">
        <div className="max-w-2xl rounded-lg border border-gray-200 p-6">
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{ priority: 0 }}
          >
            <Form.Item
              name="name"
              label="Display Name"
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
                { required: true, message: "Key is required" },
                {
                  pattern: /^[a-z][a-z0-9_]*$/,
                  message:
                    "Key must start with a letter and contain only lowercase letters, numbers, and underscores",
                },
              ]}
              extra="Machine-readable identifier. Auto-generated from name."
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
              label="Parent Role"
              extra="Inherit permissions from another role."
            >
              <Select
                allowClear
                placeholder="Select parent role (optional)"
                options={parentRoleOptions}
              />
            </Form.Item>

            <Form.Item
              name="priority"
              label="Priority"
              extra="Higher priority roles take precedence in permission conflicts (0-100)."
            >
              <InputNumber min={0} max={100} style={{ width: "100%" }} />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={isLoading}>
                  Create Role
                </Button>
                <Button onClick={() => router.push(RBAC_ROUTE)}>Cancel</Button>
              </Space>
            </Form.Item>
          </Form>
        </div>
      </Flex>
    </Layout>
  );
};

export default NewRolePage;
