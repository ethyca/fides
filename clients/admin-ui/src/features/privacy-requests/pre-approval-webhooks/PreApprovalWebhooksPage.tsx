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
} from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { PreApprovalWebhookResponse } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import {
  useCreateConnectionConfigForWebhookMutation,
  useCreateOrUpdatePreApprovalWebhooksMutation,
  useDeletePreApprovalWebhookMutation,
  useGetPreApprovalWebhooksQuery,
  useLazyGetConnectionConfigByKeyQuery,
  usePatchConnectionSecretsForWebhookMutation,
} from "./pre-approval-webhooks.slice";

const { Text } = Typography;

interface WebhookFormValues {
  name: string;
  url: string;
  authorization: string;
}

const PreApprovalWebhooksPage = () => {
  const { data, isLoading } = useGetPreApprovalWebhooksQuery();
  const [createOrUpdateWebhooks] =
    useCreateOrUpdatePreApprovalWebhooksMutation();
  const [deleteWebhook] = useDeletePreApprovalWebhookMutation();
  const [createConnectionConfig] =
    useCreateConnectionConfigForWebhookMutation();
  const [patchConnectionSecrets] =
    usePatchConnectionSecretsForWebhookMutation();
  const [getConnectionConfig] = useLazyGetConnectionConfigByKeyQuery();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] =
    useState<PreApprovalWebhookResponse | null>(null);
  const [form] = Form.useForm<WebhookFormValues>();
  const [submitting, setSubmitting] = useState(false);
  const { errorAlert, successAlert } = useAlert();

  const webhooks = useMemo(() => data?.items ?? [], [data?.items]);

  // Fetch the URL for each webhook's connection config via the dedicated endpoint
  // which returns secrets with sensitive fields redacted.
  const [urlMap, setUrlMap] = useState<Record<string, string>>({});
  const connectionKeys = useMemo(
    () =>
      webhooks
        .map((w) => w.connection_config?.key)
        .filter((k): k is string => !!k),
    [webhooks],
  );

  const fetchUrls = useCallback(async () => {
    const newMap: Record<string, string> = {};
    await Promise.all(
      connectionKeys.map(async (key) => {
        try {
          const result = await getConnectionConfig(key).unwrap();
          if (result.secrets?.url) {
            newMap[key] = result.secrets.url;
          }
        } catch {
          // silently skip — URL will show as em dash
        }
      }),
    );
    setUrlMap(newMap);
  }, [connectionKeys, getConnectionConfig]);

  useEffect(() => {
    if (connectionKeys.length > 0) {
      fetchUrls();
    }
  }, [connectionKeys, fetchUrls]);

  const openCreateModal = () => {
    setEditingWebhook(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = async (webhook: PreApprovalWebhookResponse) => {
    setEditingWebhook(webhook);
    let url = "";
    // Fetch the URL from the connection config endpoint (returns secrets with
    // sensitive fields redacted).
    if (webhook.connection_config?.key) {
      try {
        const config = await getConnectionConfig(
          webhook.connection_config.key,
        ).unwrap();
        url = config.secrets?.url ?? "";
      } catch {
        // fall back to empty
      }
    }
    form.setFieldsValue({
      name: webhook.name,
      url,
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
    setSubmitting(true);
    try {
      const connectionKey = editingWebhook?.connection_config?.key
        ? editingWebhook.connection_config.key
        : `pre_approval_${values.name.toLowerCase().replace(/\s+/g, "_")}`;

      // Step 1: Create or update the HTTPS connection config
      const connectionResult = await createConnectionConfig({
        key: connectionKey,
        name: `Pre-Approval: ${values.name}`,
        connection_type: "https",
        access: "read",
      });
      if (isErrorResult(connectionResult)) {
        errorAlert(getErrorMessage(connectionResult.error));
        return;
      }

      // Step 2: Set the connection secrets (URL and authorization header).
      // Use PATCH so that omitting authorization preserves the existing value.
      const secrets: Record<string, string> = { url: values.url };
      if (values.authorization) {
        secrets.authorization = values.authorization;
      }
      const secretsResult = await patchConnectionSecrets({
        connectionKey,
        secrets,
      });
      if (isErrorResult(secretsResult)) {
        errorAlert(getErrorMessage(secretsResult.error));
        return;
      }

      // Step 3: Create or update the pre-approval webhook
      const webhookPayload = {
        name: values.name,
        connection_config_key: connectionKey,
        ...(editingWebhook?.key ? { key: editingWebhook.key } : {}),
      };
      const webhookResult = await createOrUpdateWebhooks([webhookPayload]);
      if (isErrorResult(webhookResult)) {
        errorAlert(getErrorMessage(webhookResult.error));
        return;
      }

      successAlert(
        editingWebhook
          ? "Pre-approval webhook updated"
          : "Pre-approval webhook created",
      );
      handleCancel();
    } catch {
      errorAlert("An unexpected error occurred");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (webhookKey: string) => {
    const result = await deleteWebhook(webhookKey);
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert("Pre-approval webhook deleted");
    }
  };

  const getWebhookUrl = (record: PreApprovalWebhookResponse): string =>
    (record.connection_config?.key && urlMap[record.connection_config.key]) ||
    "—";

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "URL",
      key: "url",
      render: (_: unknown, record: PreApprovalWebhookResponse) => {
        const url = getWebhookUrl(record);
        return url === "—" ? (
          <Text type="secondary">{url}</Text>
        ) : (
          <Text>{url}</Text>
        );
      },
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
            rules={[{ required: true, message: "Please enter a webhook name" }]}
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
            <Button type="primary" htmlType="submit" loading={submitting}>
              {editingWebhook ? "Update" : "Create"}
            </Button>
          </Flex>
        </Form>
      </Modal>
    </Flex>
  );
};

export default PreApprovalWebhooksPage;
