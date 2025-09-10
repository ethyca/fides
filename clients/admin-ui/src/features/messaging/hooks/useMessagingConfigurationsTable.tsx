import type { ColumnsType } from "antd/es/table";
import { isErrorResult } from "common/helpers";
import { useAPIHelper } from "common/hooks";
import {
  AntButton as Button,
  AntMessage as message,
  AntModal as Modal,
  AntSpace as Space,
  AntSwitch as Switch,
  AntTooltip as Tooltip,
  HStack,
  Icons,
  Text,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { MESSAGING_PROVIDERS_EDIT_ROUTE } from "~/features/common/nav/routes";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { usePatchConfigurationSettingsMutation } from "~/features/config-settings/config-settings.slice";
import {
  MessagingConfigResponse,
  MessagingServiceType,
  ScopeRegistryEnum,
} from "~/types/api";

import { useHasPermission } from "../../common/Restrict";
import AwsIcon from "../icons/AwsIcon";
import MailgunIcon from "../icons/MailgunIcon";
import TwilioIcon from "../icons/TwilioIcon";
import {
  useDeleteMessagingConfigurationByKeyMutation,
  useGetActiveMessagingProviderQuery,
  useGetMessagingConfigurationsQuery,
} from "../messaging.slice";
import MessagingVerificationStatusCell from "../MessagingTestStatusCell";

// Define column keys for type safety
enum MessagingConfigurationColumnKeys {
  NAME = "name",
  VERIFICATION_STATUS = "verification_status",
  ENABLED = "enabled",
  ACTIONS = "actions",
}

export const useMessagingConfigurationsTable = () => {
  const router = useRouter();
  const { handleError } = useAPIHelper();
  const [messagingValue, setMessagingValue] = useState<string | null>(null);
  const [saveActiveConfiguration] = usePatchConfigurationSettingsMutation();
  const [deleteMessagingConfiguration] =
    useDeleteMessagingConfigurationByKeyMutation();

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE,
  ]);

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [configToDelete, setConfigToDelete] = useState<{
    key: string;
    name: string;
  } | null>(null);

  // Table state management with URL sync
  const tableState = useTableState<MessagingConfigurationColumnKeys>({
    pagination: {
      defaultPageSize: 25,
      pageSizeOptions: [25, 50, 100],
    },
    sorting: {
      validColumns: Object.values(MessagingConfigurationColumnKeys),
      defaultSortKey: MessagingConfigurationColumnKeys.NAME,
      defaultSortOrder: "ascend",
    },
  });

  // API queries
  const { data: activeMessagingProvider, isLoading: isActiveProviderLoading } =
    useGetActiveMessagingProviderQuery();

  // TODO: When the API supports pagination/search/sorting, pass tableState.state here
  // const { data, isLoading: isConfigurationsLoading } = useGetMessagingConfigurationsQuery(tableState.state);
  const { data, isLoading: isConfigurationsLoading } =
    useGetMessagingConfigurationsQuery();

  // Set initial messaging value from active provider
  useEffect(() => {
    if (activeMessagingProvider) {
      setMessagingValue(activeMessagingProvider.service_type);
    } else {
      setMessagingValue(null);
    }
  }, [activeMessagingProvider]);

  // Business actions
  const setActiveServiceType = useCallback(
    async (serviceType: MessagingServiceType | null) => {
      try {
        const result = await saveActiveConfiguration({
          notifications: {
            notification_service_type: serviceType,
          },
        });
        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          // Update local state immediately for responsive UI
          setMessagingValue(serviceType);
          message.success(
            serviceType
              ? "Updated active messaging config"
              : "Disabled active messaging config",
          );
        }
      } catch (error) {
        // Handle any other errors that might occur
        handleError(error);
      }
    },
    [saveActiveConfiguration, handleError, setMessagingValue],
  );

  const handleEditConfiguration = useCallback(
    (messagingConfig: MessagingConfigResponse) => {
      const editPath = MESSAGING_PROVIDERS_EDIT_ROUTE.replace(
        "[key]",
        messagingConfig.key,
      );
      router.push({
        pathname: editPath,
        query: {
          last_test_succeeded: messagingConfig.last_test_succeeded ?? "",
          last_test_timestamp: messagingConfig.last_test_timestamp ?? "",
        },
      });
    },
    [router],
  );

  const handleDeleteConfiguration = useCallback((key: string, name: string) => {
    setConfigToDelete({ key, name });
    setDeleteModalOpen(true);
  }, []);

  const confirmDelete = useCallback(async () => {
    if (!configToDelete) {
      return;
    }

    try {
      const result = await deleteMessagingConfiguration({
        key: configToDelete.key,
      });
      if (isErrorResult(result)) {
        handleError(result.error);
      } else {
        message.success("Messaging configuration successfully deleted");
      }
    } catch (error) {
      handleError(error);
    } finally {
      setDeleteModalOpen(false);
      setConfigToDelete(null);
    }
  }, [configToDelete, deleteMessagingConfiguration, handleError]);

  const cancelDelete = useCallback(() => {
    setDeleteModalOpen(false);
    setConfigToDelete(null);
  }, []);

  // Ant Design table integration
  const antTableConfig = useMemo(
    () => ({
      enableSelection: false, // No bulk actions needed for messaging configs
      getRowKey: (record: MessagingConfigResponse) => record.key,
      isLoading: isConfigurationsLoading || isActiveProviderLoading,
      dataSource: data?.items || [],
      totalRows: data?.total || 0,
      customTableProps: {
        size: "small" as const,
        pagination: {
          hideOnSinglePage: true,
          showSizeChanger: true,
          pageSizeOptions: ["25", "50", "100"],
        },
      },
    }),
    [
      isConfigurationsLoading,
      isActiveProviderLoading,
      data?.items,
      data?.total,
    ],
  );

  const antTable = useAntTable<
    MessagingConfigResponse,
    MessagingConfigurationColumnKeys
  >(tableState, antTableConfig);

  // Column definitions
  const columns: ColumnsType<MessagingConfigResponse> = useMemo(
    () => [
      {
        title: "Provider type",
        dataIndex: "name",
        key: MessagingConfigurationColumnKeys.NAME,
        render: (name: string, record: MessagingConfigResponse) => {
          const getProviderIcon = () => {
            switch (record.service_type) {
              case "mailgun":
                return <MailgunIcon />;
              case "twilio_text":
              case "twilio_email":
                return <TwilioIcon />;
              case "aws_ses":
                return <AwsIcon />;
              default:
                return <TwilioIcon />; // fallback
            }
          };

          return (
            <HStack>
              {getProviderIcon()}
              <Text>{name}</Text>
            </HStack>
          );
        },
      },
      {
        title: "Verification status",
        key: MessagingConfigurationColumnKeys.VERIFICATION_STATUS,
        render: (_, record: MessagingConfigResponse) => (
          <MessagingVerificationStatusCell messagingConfig={record} />
        ),
      },
      {
        title: "Enabled",
        key: MessagingConfigurationColumnKeys.ENABLED,
        width: 100,
        render: (_, record: MessagingConfigResponse) => {
          const isEnabled = record.service_type === messagingValue;
          const hasFailedTest =
            Boolean(record.last_test_timestamp) &&
            record.last_test_timestamp !== "" &&
            record.last_test_succeeded === false;
          // Disable switch only if last test failed AND the provider is currently OFF (can't enable)
          const isDisabled = hasFailedTest && !isEnabled;

          const switchElement = (
            <Switch
              checked={isEnabled}
              disabled={isDisabled}
              onChange={(checked) => {
                if (checked) {
                  setActiveServiceType(record.service_type);
                } else {
                  setActiveServiceType(null);
                }
              }}
            />
          );

          if (isDisabled) {
            return (
              <Tooltip title="This provider cannot be enabled because its last test failed. Please fix the configuration and test again.">
                {switchElement}
              </Tooltip>
            );
          }

          return switchElement;
        },
      },
      {
        title: "Actions",
        key: MessagingConfigurationColumnKeys.ACTIONS,
        render: (_, record: MessagingConfigResponse) => (
          <HStack>
            {userCanUpdate && (
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleEditConfiguration(record);
                }}
                size="small"
                icon={<Icons.Edit />}
                title="Edit"
                aria-label="Edit messaging configuration"
                data-testid="edit-messaging-config-btn"
              />
            )}
            {userCanUpdate && (
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConfiguration(record.key, record.name);
                }}
                size="small"
                icon={<Icons.TrashCan />}
                title="Delete"
                aria-label="Delete messaging configuration"
                data-testid="delete-messaging-config-btn"
              />
            )}
          </HStack>
        ),
      },
    ],
    [
      userCanUpdate,
      messagingValue,
      handleEditConfiguration,
      handleDeleteConfiguration,
      setActiveServiceType,
    ],
  );

  // Delete confirmation modal
  const deleteModal = useMemo(
    () => (
      <Modal
        title="Delete messaging configuration"
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
            Are you sure you want to delete &quot;
            <strong>{configToDelete?.name}</strong>&quot; messaging
            configuration?
          </Text>
          <Text>This action cannot be undone.</Text>
        </Space>
      </Modal>
    ),
    [deleteModalOpen, configToDelete?.name, cancelDelete, confirmDelete],
  );

  return {
    // Table state and data
    columns,

    // Ant Design table integration
    tableProps: antTable.tableProps,
    selectionProps: antTable.selectionProps,

    // Business state
    userCanUpdate,
    isLoading: isConfigurationsLoading || isActiveProviderLoading,

    // Modal components
    deleteModal,

    // Business actions (exposed for potential future use)
    handleEditConfiguration,
    handleDeleteConfiguration,
    setActiveServiceType,
  };
};
