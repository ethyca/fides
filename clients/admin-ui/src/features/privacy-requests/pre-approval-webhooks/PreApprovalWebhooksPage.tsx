import {
  Button,
  Flex,
  Form,
  Icons,
  Input,
  Modal,
  Skeleton,
  Table,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  useGetDatastoreConnectionByKeyQuery,
  usePatchDatastoreConnectionMutation,
  usePatchDatastoreConnectionSecretsMutation,
} from "~/features/datastore-connections/datastore-connection.slice";
import { getErrorMessage } from "~/features/common/helpers";
import { PreApprovalWebhookResponse } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import {
  useCreateOrUpdatePreApprovalWebhooksMutation,
  useDeletePreApprovalWebhookMutation,
  useGetPreApprovalWebhooksQuery,
} from "./pre-approval-webhooks.slice";

const { Text } = Typography;

interface WebhookFormValues {
  name: string;
  url: string;
  authorization: string;
}

const WebhookUrlCell = ({
  connectionKey,
}: {
  connectionKey: string | undefined;
}) => {
  const { data } = useGetDatastoreConnectionByKeyQuery(connectionKey!, {
    skip: !connectionKey,
  });
  const url = (data as Record<string, unknown>)?.secrets
    ? ((data as Record<string, unknown>).secrets as Record<string, string>)?.url
    : undefined;

  return url ? <Text>{url}</Text> : <Text type="secondary">&mdash;</Text>;
};

const PreApprovalWebhooksPage = () => {
  const { data, isLoading } = useGetPreApprovalWebhooksQuery();
  const [createOrUpdateWebhooks, { isLoading: isCreating }] =
    useCreateOrUpdatePreApprovalWebhooksMutation();
  const [deleteWebhook] = useDeletePreApprovalWebhookMutation();
  const [patchConnection] = usePatchDatastoreConnectionMutation();
  const [patchSecrets] = usePatchDatastoreConnectionSecretsMutation();
  const message = useMessage();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] =
    useState<PreApprovalWebhookResponse | null>(null);
  const [form] = Form.useForm<WebhookFormValues>();

  const webhooks = data?.items ?? [];

  const openCreateModal = () => {
    setEditingWebhook(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = (webhook: PreApprovalWebhookResponse) => {
    setEditingWebhook(webhook);
    form.setFieldsValue({
      name: webhook.name,
      url: "",
      authorization: "",
    });
    setIsModalOpen(true);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    setEditingWebhook(null);
    form.resetFields();
  };

  const handleSubmit = async (values: WebhookFormValues) => {
    try {
      const connectionKey = editingWebhook?.connection_config?.key
        ? editingWebhook.connection_config.key
        : `pre_approval_${values.name.toLowerCase().replace(/[^a-z0-9]+/g, "_")}`;

      const connectionResult = await patchConnection({
        key: connectionKey,
        name: `Pre-Approval: ${values.name}`,
        connection_type: "https",
        access: "read",
      } as any);
      if (isErrorResult(connectionResult)) {
        message.error(getErrorMessage(connectionResult.error));
        return;
      }

      const secrets: Record<string, string> = { url: values.url };
      if (values.authorization) {
        secrets.authorization = values.authorization;
      }
      const secretsResult = await patchSecrets({
        connection_key: connectionKey,
        secrets,
      });
      if (isErrorResult(secretsResult)) {
        message.error(getErrorMessage(secretsResult.error));
        return;
      }

      const webhookPayload = {
        name: values.name,
        connection_config_key: connectionKey,
        ...(editingWebhook?.key ? { key: editingWebhook.key } : {}),
      };
      const webhookResult = await createOrUpdateWebhooks([webhookPayload]);
      if (isErrorResult(webhookResult)) {
        message.error(getErrorMessage(webhookResult.error));
        return;
      }

      message.success(
        editingWebhook
          ? "Pre-approval webhook updated"
          : "Pre-approval webhook created",
      );
      handleCancel();
    } catch {
      message.error("An unexpected error occurred");
    }
  };

  const handleDelete = async (webhookKey: string) => {
    const result = await deleteWebhook(webhookKey);
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success("Pre-approval webhook deleted");
    }
  };

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "URL",
      key: "url",
      render: (_: unknown, record: PreApprovalWebhookResponse) => (
        <WebhookUrlCell connectionKey={record.connection_config?.key} />
      ),
    },
    {
      title: "Actions",
      key: "actions",
      width: 100,
      render: (_: unknown, record: PreApprovalWebhookResponse) => (
        <Flex gap={8}>
          <Tooltip title="Edit">
            <Button
              size="small"
              icon={<Icons.Edit />}
              aria-label="Edit webhook"
              onClick={() => openEditModal(record)}
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Button
              size="small"
              icon={<Icons.TrashCan />}
              aria-label="Delete webhook"
              onClick={() => {
                Modal.confirm({
                  title: "Delete this webhook?",
                  content: "This action cannot be undone.",
                  okText: "Delete",
                  cancelText: "Cancel",
                  okButtonProps: { danger: true },
                  onOk: () => record.key && handleDelete(record.key),
                });
              }}
            />
          </Tooltip>
        </Flex>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton active />;
  }

  return (
    <Flex vertical gap="middle">
      <Flex justify="space-between" align="center">
        <Text>
          Configure external webhooks that are called before a privacy request
          is automatically approved. External systems can respond to mark a
          request as eligible or not eligible for automatic approval.
        </Text>
      </Flex>

      <Flex justify="flex-end">
        <Button type="primary" onClick={openCreateModal}>
          Add webhook
        </Button>
      </Flex>

      <Table
        columns={columns}
        dataSource={webhooks}
        rowKey="key"
        pagination={false}
        locale={{
          emptyText: "No pre-approval webhooks configured",
        }}
      />

      <Modal
        title={editingWebhook ? "Edit webhook" : "Add webhook"}
        open={isModalOpen}
        onCancel={handleCancel}
        footer={null}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          autoComplete="off"
        >
          <Form.Item
            label="Webhook name"
            name="name"
            rules={[
              { required: true, message: "Please enter a webhook name" },
            ]}
          >
            <Input placeholder="e.g. Identity Verification Service" />
          </Form.Item>

          <Form.Item
            label="Endpoint URL"
            name="url"
            rules={[
              { required: true, message: "Please enter an endpoint URL" },
              { type: "url", message: "Please enter a valid URL" },
            ]}
          >
            <Input placeholder="https://example.com/webhook" />
          </Form.Item>

          <Form.Item
            label="Authorization header"
            name="authorization"
            help={
              editingWebhook
                ? "Leave blank to keep the existing authorization value"
                : undefined
            }
          >
            <Input.Password
              placeholder="Bearer token or API key"
              visibilityToggle
            />
          </Form.Item>

          <Flex justify="flex-end" gap="small">
            <Button onClick={handleCancel}>Cancel</Button>
            <Button type="primary" htmlType="submit" loading={isCreating}>
              {editingWebhook ? "Update" : "Create"}
            </Button>
          </Flex>
        </Form>
      </Modal>
    </Flex>
  );
};

export default PreApprovalWebhooksPage;
