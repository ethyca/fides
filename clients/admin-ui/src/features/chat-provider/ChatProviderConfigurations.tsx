/* eslint-disable react/no-unstable-nested-components */
import type { ColumnsType } from "antd/es/table";
import {
  Button,
  Flex,
  Icons,
  Modal,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { CHAT_PROVIDERS_CONFIGURE_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { TableSkeletonLoader } from "~/features/common/table/v2";
import { ScopeRegistryEnum } from "~/types/api";

import {
  ChatProviderSettingsResponse,
  useDeleteChatConfigMutation,
  useEnableChatConfigMutation,
  useGetChatConfigsQuery,
} from "./chatProvider.slice";
import SlackIcon from "./icons/SlackIcon";

const { Text } = Typography;

// Define column keys for type safety
enum ChatProviderColumnKeys {
  PROVIDER = "provider",
  STATUS = "status",
  ENABLED = "enabled",
  ACTIONS = "actions",
}

const EmptyTableNotice = () => {
  return (
    <Space
      direction="vertical"
      size="middle"
      data-testid="no-results-notice"
      style={{
        margin: "24px auto",
        padding: "40px",
        maxWidth: "70%",
        textAlign: "center",
      }}
    >
      <Text strong>No chat providers found.</Text>
      <Text>
        Click &quot;Add a chat provider&quot; to configure Slack or other chat
        integrations.
      </Text>
    </Space>
  );
};

export const ChatProviderConfigurations = () => {
  const router = useRouter();
  const message = useMessage();
  const { data: configsData, isLoading, refetch } = useGetChatConfigsQuery();
  const [deleteConfig] = useDeleteChatConfigMutation();
  const [enableConfig] = useEnableChatConfigMutation();

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE,
  ]);

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [configToDelete, setConfigToDelete] =
    useState<ChatProviderSettingsResponse | null>(null);

  // Use items from the list response
  const tableData = useMemo(() => {
    return configsData?.items ?? [];
  }, [configsData]);

  const handleEditConfiguration = useCallback(
    (configId: string) => {
      router.push(`${CHAT_PROVIDERS_CONFIGURE_ROUTE}?id=${configId}`);
    },
    [router],
  );

  const handleDeleteConfiguration = useCallback(
    (config: ChatProviderSettingsResponse) => {
      setConfigToDelete(config);
      setDeleteModalOpen(true);
    },
    [],
  );

  const handleEnableConfiguration = useCallback(
    async (configId: string) => {
      try {
        const result = await enableConfig(configId);
        if (isErrorResult(result)) {
          message.error(getErrorMessage(result.error, "Failed to enable"));
        } else {
          message.success("Chat provider enabled");
          refetch();
        }
      } catch {
        message.error("Failed to enable chat provider");
      }
    },
    [enableConfig, message, refetch],
  );

  const confirmDelete = useCallback(async () => {
    if (!configToDelete) {
      return;
    }
    try {
      const result = await deleteConfig(configToDelete.id);
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error, "Failed to delete"));
      } else {
        message.success("Chat provider deleted successfully");
        refetch();
      }
    } finally {
      setDeleteModalOpen(false);
      setConfigToDelete(null);
    }
  }, [configToDelete, deleteConfig, message, refetch]);

  const cancelDelete = useCallback(() => {
    setDeleteModalOpen(false);
    setConfigToDelete(null);
  }, []);

  // Column definitions
  const columns: ColumnsType<ChatProviderSettingsResponse> = useMemo(
    () => [
      {
        title: "Provider",
        key: ChatProviderColumnKeys.PROVIDER,
        render: (_: unknown, record: ChatProviderSettingsResponse) => {
          const getProviderIcon = () => {
            switch (record.provider_type) {
              case "slack":
                return <SlackIcon />;
              default:
                return <SlackIcon />;
            }
          };

          // Display as "Slack (workspace_name)" if authorized, otherwise "Slack (workspace_url)"
          const providerLabel =
            record.provider_type.charAt(0).toUpperCase() +
            record.provider_type.slice(1);

          let displayName = providerLabel;
          if (record.workspace_name) {
            displayName = `${providerLabel} (${record.workspace_name})`;
          } else if (record.workspace_url) {
            displayName = `${providerLabel} (${record.workspace_url})`;
          }

          return (
            <Space>
              {getProviderIcon()}
              <Text>{displayName}</Text>
            </Space>
          );
        },
      },
      {
        title: "Status",
        key: ChatProviderColumnKeys.STATUS,
        render: (_, record: ChatProviderSettingsResponse) => {
          if (record.authorized) {
            return (
              <Tag color="success" data-testid="status-authorized">
                Authorized
              </Tag>
            );
          }
          if (record.client_id) {
            return (
              <Tag color="warning" data-testid="status-not-authorized">
                Not authorized
              </Tag>
            );
          }
          return <Tag data-testid="status-not-configured">Not configured</Tag>;
        },
      },
      {
        title: "Enabled",
        key: ChatProviderColumnKeys.ENABLED,
        width: 100,
        render: (_, record: ChatProviderSettingsResponse) => (
          <Switch
            checked={record.enabled}
            disabled={!userCanUpdate || record.enabled}
            onChange={() => {
              if (!record.enabled) {
                handleEnableConfiguration(record.id);
              }
            }}
            title={
              record.enabled
                ? "This provider is currently active"
                : "Click to enable this provider"
            }
          />
        ),
      },
      {
        title: "Actions",
        key: ChatProviderColumnKeys.ACTIONS,
        render: (_, record: ChatProviderSettingsResponse) => (
          <Space>
            {userCanUpdate && !record.authorized && record.client_id && (
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  window.location.href = `/api/v1/plus/chat/authorize?config_id=${record.id}`;
                }}
                size="small"
                type="primary"
                title="Authorize with Slack"
                aria-label="Authorize with Slack"
                data-testid="authorize-chat-config-btn"
              >
                Authorize
              </Button>
            )}
            {userCanUpdate && (
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleEditConfiguration(record.id);
                }}
                size="small"
                icon={<Icons.Edit />}
                title="Edit"
                aria-label="Edit chat provider configuration"
                data-testid="edit-chat-config-btn"
              />
            )}
            {userCanUpdate && (
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConfiguration(record);
                }}
                size="small"
                icon={<Icons.TrashCan />}
                title="Delete"
                aria-label="Delete chat provider"
                data-testid="delete-chat-config-btn"
              />
            )}
          </Space>
        ),
      },
    ],
    [
      userCanUpdate,
      handleEditConfiguration,
      handleDeleteConfiguration,
      handleEnableConfiguration,
    ],
  );

  // Delete confirmation modal
  const deleteModal = useMemo(
    () => (
      <Modal
        title="Delete chat provider"
        open={deleteModalOpen}
        onCancel={cancelDelete}
        footer={[
          <Button key="cancel" onClick={cancelDelete}>
            Cancel
          </Button>,
          <Button key="delete" type="primary" danger onClick={confirmDelete}>
            Delete
          </Button>,
        ]}
      >
        <Space direction="vertical">
          <Text>
            Are you sure you want to delete the Slack provider for{" "}
            <strong>
              {configToDelete?.workspace_name ?? configToDelete?.workspace_url}
            </strong>
            ?
          </Text>
          <Text>This action cannot be undone.</Text>
        </Space>
      </Modal>
    ),
    [deleteModalOpen, configToDelete, cancelDelete, confirmDelete],
  );

  return (
    <>
      <Text className="mb-8" style={{ maxWidth: "70%" }}>
        Configure chat providers to enable notifications, alerts, and AI-powered
        privacy assessment questionnaires through platforms like Slack.
      </Text>
      <Flex flex={1} vertical style={{ overflow: "auto" }}>
        {userCanUpdate && (
          <Flex justify="flex-end" className="mb-4 w-full">
            <Button
              onClick={() => {
                router.push(CHAT_PROVIDERS_CONFIGURE_ROUTE);
              }}
              role="link"
              type="primary"
              icon={<Icons.Add />}
              iconPosition="end"
              data-testid="add-chat-provider-btn"
            >
              Add a chat provider
            </Button>
          </Flex>
        )}
        {isLoading ? (
          <TableSkeletonLoader rowHeight={36} numRows={3} />
        ) : (
          <Table
            dataSource={tableData}
            columns={columns}
            rowKey="id"
            size="small"
            pagination={false}
            locale={{
              emptyText: <EmptyTableNotice />,
            }}
          />
        )}
      </Flex>

      {deleteModal}
    </>
  );
};

export default ChatProviderConfigurations;
