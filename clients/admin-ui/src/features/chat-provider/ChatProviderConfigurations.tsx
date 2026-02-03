/* eslint-disable react/no-unstable-nested-components */
import {
  Button,
  ChakraFlex as Flex,
  ChakraHStack as HStack,
  ChakraText as Text,
  ChakraVStack as VStack,
  Icons,
  Modal,
  Space,
  Switch,
  Table,
  Tag,
  useMessage,
} from "fidesui";
import type { ColumnsType } from "antd/es/table";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { CHAT_PROVIDERS_CONFIGURE_ROUTE } from "~/features/common/nav/routes";
import { TableSkeletonLoader } from "~/features/common/table/v2";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";

import {
  ChatProviderSettingsResponse,
  useDeleteChatConnectionMutation,
  useGetChatSettingsQuery,
} from "./chatProvider.slice";
import SlackIcon from "./icons/SlackIcon";

// Define column keys for type safety
enum ChatProviderColumnKeys {
  NAME = "name",
  STATUS = "status",
  ENABLED = "enabled",
  ACTIONS = "actions",
}

const EmptyTableNotice = () => {
  return (
    <VStack
      mt={6}
      p={10}
      spacing={4}
      borderRadius="base"
      maxW="70%"
      data-testid="no-results-notice"
      alignSelf="center"
      margin="auto"
    >
      <VStack>
        <Text fontSize="md" fontWeight="600">
          No chat providers found.
        </Text>
        <Text fontSize="sm">
          Click &quot;Add a chat provider&quot; to configure Slack or other chat
          integrations.
        </Text>
      </VStack>
    </VStack>
  );
};

export const ChatProviderConfigurations = () => {
  const router = useRouter();
  const message = useMessage();
  const { data: settings, isLoading, refetch } = useGetChatSettingsQuery();
  const [deleteConnection] = useDeleteChatConnectionMutation();

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE,
  ]);

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  // Transform single config into array for table
  const tableData = useMemo(() => {
    if (!settings || !settings.client_id) {
      return [];
    }
    return [settings];
  }, [settings]);

  const handleEditConfiguration = useCallback(() => {
    router.push(CHAT_PROVIDERS_CONFIGURE_ROUTE);
  }, [router]);

  const handleDeleteConfiguration = useCallback(() => {
    setDeleteModalOpen(true);
  }, []);

  const confirmDelete = useCallback(async () => {
    try {
      const result = await deleteConnection();
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error, "Failed to disconnect"));
      } else {
        message.success("Chat provider disconnected successfully");
        refetch();
      }
    } finally {
      setDeleteModalOpen(false);
    }
  }, [deleteConnection, message, refetch]);

  const cancelDelete = useCallback(() => {
    setDeleteModalOpen(false);
  }, []);

  // Column definitions
  const columns: ColumnsType<ChatProviderSettingsResponse> = useMemo(
    () => [
      {
        title: "Provider type",
        dataIndex: "provider_type",
        key: ChatProviderColumnKeys.NAME,
        render: (providerType: string, record: ChatProviderSettingsResponse) => {
          const getProviderIcon = () => {
            switch (providerType) {
              case "slack":
                return <SlackIcon />;
              default:
                return <SlackIcon />;
            }
          };

          const getProviderName = () => {
            switch (providerType) {
              case "slack":
                return record.workspace_name
                  ? `Slack (${record.workspace_name})`
                  : "Slack";
              default:
                return providerType;
            }
          };

          return (
            <HStack>
              {getProviderIcon()}
              <Text>{getProviderName()}</Text>
            </HStack>
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
          return (
            <Tag data-testid="status-not-configured">
              Not configured
            </Tag>
          );
        },
      },
      {
        title: "Enabled",
        key: ChatProviderColumnKeys.ENABLED,
        width: 100,
        render: (_, record: ChatProviderSettingsResponse) => (
          <Switch checked={record.enabled} disabled />
        ),
      },
      {
        title: "Actions",
        key: ChatProviderColumnKeys.ACTIONS,
        render: (_, record: ChatProviderSettingsResponse) => (
          <HStack>
            {userCanUpdate && (
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleEditConfiguration();
                }}
                size="small"
                icon={<Icons.Edit />}
                title="Edit"
                aria-label="Edit chat provider configuration"
                data-testid="edit-chat-config-btn"
              />
            )}
            {userCanUpdate && record.authorized && (
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConfiguration();
                }}
                size="small"
                icon={<Icons.TrashCan />}
                title="Disconnect"
                aria-label="Disconnect chat provider"
                data-testid="delete-chat-config-btn"
              />
            )}
          </HStack>
        ),
      },
    ],
    [userCanUpdate, handleEditConfiguration, handleDeleteConfiguration],
  );

  // Delete confirmation modal
  const deleteModal = useMemo(
    () => (
      <Modal
        title="Disconnect chat provider"
        open={deleteModalOpen}
        onCancel={cancelDelete}
        footer={[
          <Button key="cancel" onClick={cancelDelete}>
            Cancel
          </Button>,
          <Button key="delete" type="primary" danger onClick={confirmDelete}>
            Disconnect
          </Button>,
        ]}
      >
        <Space direction="vertical">
          <Text>
            Are you sure you want to disconnect{" "}
            <strong>
              {settings?.workspace_name
                ? `Slack (${settings.workspace_name})`
                : "Slack"}
            </strong>
            ?
          </Text>
          <Text>
            Your OAuth credentials will be preserved, but you will need to
            re-authorize to use the integration.
          </Text>
        </Space>
      </Modal>
    ),
    [deleteModalOpen, settings?.workspace_name, cancelDelete, confirmDelete],
  );

  return (
    <>
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "70%" }}>
        Configure chat providers to enable notifications, alerts, and AI-powered
        privacy assessment questionnaires through platforms like Slack.
      </Text>
      <Flex flex={1} direction="column" overflow="auto">
        {userCanUpdate && (
          <Space
            direction="horizontal"
            style={{
              width: "100%",
              justifyContent: "flex-end",
              marginBottom: 16,
            }}
          >
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
          </Space>
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
