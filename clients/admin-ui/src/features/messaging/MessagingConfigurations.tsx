/* eslint-disable react/no-unstable-nested-components */
import type { ColumnsType } from "antd/es/table";
import { isErrorResult } from "common/helpers";
import { useAPIHelper } from "common/hooks";
import {
  AntButton as Button,
  AntMessage as message,
  AntModal as Modal,
  AntSpace as Space,
  AntSwitch as Switch,
  AntTable as Table,
  AntTooltip as Tooltip,
  Flex,
  Heading,
  HStack,
  Icons,
  Text,
  VStack,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import {
  MESSAGING_PROVIDERS_EDIT_ROUTE,
  MESSAGING_PROVIDERS_ROUTE,
} from "~/features/common/nav/routes";
import { usePatchConfigurationSettingsMutation } from "~/features/config-settings/config-settings.slice";
import {
  MessagingConfigResponse,
  MessagingServiceType,
  ScopeRegistryEnum,
} from "~/types/api";

import { useHasPermission } from "../common/Restrict";
import { TableSkeletonLoader } from "../common/table/v2";
import MailgunIcon from "./MailgunIcon";
import {
  useDeleteMessagingConfigurationByKeyMutation,
  useGetActiveMessagingProviderQuery,
  useGetMessagingConfigurationsQuery,
} from "./messaging.slice";
import MessagingTestStatusCell from "./MessagingTestStatusCell";
import { TestMessagingProviderModal } from "./TestMessagingProviderModal";
import TwilioIcon from "./TwilioIcon";

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
          No messaging providers found.
        </Text>
        <Text fontSize="sm">
          Click &quot;Add a messaging provider&quot; to add your first messaging
          provider to Fides.
        </Text>
      </VStack>
    </VStack>
  );
};

export const MessagingConfigurations = () => {
  const router = useRouter();
  const { handleError } = useAPIHelper();
  const [messagingValue, setMessagingValue] = useState<string | null>(null);
  const [saveActiveConfiguration] = usePatchConfigurationSettingsMutation();
  const [deleteMessagingConfiguration] =
    useDeleteMessagingConfigurationByKeyMutation();
  const { data: activeMessagingProvider, isLoading: isActiveProviderLoading } =
    useGetActiveMessagingProviderQuery();

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE,
  ]);

  const [selectedServiceType, setSelectedServiceType] =
    useState<MessagingConfigResponse["service_type"]>();
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [configToDelete, setConfigToDelete] = useState<{
    key: string;
    name: string;
  } | null>(null);

  const { data, isLoading: isConfigurationsLoading } =
    useGetMessagingConfigurationsQuery();

  useEffect(() => {
    if (activeMessagingProvider) {
      setMessagingValue(activeMessagingProvider.service_type);
    } else {
      setMessagingValue(null);
    }
  }, [activeMessagingProvider]);

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
      router.push(editPath);
    },
    [router],
  );

  const handleDeleteConfiguration = useCallback((key: string, name: string) => {
    setConfigToDelete({ key, name });
    setDeleteModalOpen(true);
  }, []);

  const confirmDelete = async () => {
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
  };

  const cancelDelete = () => {
    setDeleteModalOpen(false);
    setConfigToDelete(null);
  };

  const columns: ColumnsType<MessagingConfigResponse> = useMemo(
    () => [
      {
        title: "Provider type",
        dataIndex: "name",
        key: "name",
        render: (name: string, record: MessagingConfigResponse) => (
          <HStack>
            {record.service_type === "mailgun" ? (
              <MailgunIcon />
            ) : (
              <TwilioIcon />
            )}
            <Text>{name}</Text>
          </HStack>
        ),
      },
      {
        title: "Test status",
        key: "test_status",
        render: (_, record: MessagingConfigResponse) => (
          <MessagingTestStatusCell messagingConfig={record} />
        ),
      },
      {
        title: "Enabled",
        key: "enabled",
        width: 100,
        render: (_, record: MessagingConfigResponse) => {
          const isEnabled = record.service_type === messagingValue;
          const hasFailedTest =
            Boolean(record.last_test_timestamp) &&
            record.last_test_timestamp !== "" &&
            record.last_test_succeeded === false;
          const isDisabled = Boolean(hasFailedTest);

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
        key: "actions",
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

  const isLoading = isConfigurationsLoading || isActiveProviderLoading;

  return (
    <Layout title="Messaging providers">
      <Heading mb={5} fontSize="2xl" fontWeight="semibold">
        Manage messaging providers
      </Heading>
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "70%" }}>
        Fides requires a messaging provider for sending processing notices to
        privacy request subjects, and allows for Subject Identity Verification
        in privacy requests. Please follow the{" "}
        <Text as="span" color="complimentary.500">
          documentation
        </Text>{" "}
        to setup a messaging service that Fides supports. Ensure you have
        completed the setup for the preferred messaging provider and have the
        details handy prior to the following steps.
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
              href={`${MESSAGING_PROVIDERS_ROUTE}/new`}
              role="link"
              type="primary"
              icon={<Icons.Add />}
              iconPosition="end"
              data-testid="add-messaging-provider-btn"
            >
              Add a messaging provider
            </Button>
          </Space>
        )}
        {isLoading ? (
          <TableSkeletonLoader rowHeight={36} numRows={5} />
        ) : (
          <Table
            columns={columns}
            dataSource={data?.items ?? []}
            rowKey="key"
            pagination={{
              hideOnSinglePage: true,
              showSizeChanger: true,
              pageSizeOptions: ["25", "50", "100"],
            }}
            locale={{
              emptyText: <EmptyTableNotice />,
            }}
            size="small"
          />
        )}
      </Flex>
      {!!selectedServiceType && (
        <TestMessagingProviderModal
          serviceType={selectedServiceType}
          isOpen={!!selectedServiceType}
          onClose={() => setSelectedServiceType(undefined)}
        />
      )}
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
    </Layout>
  );
};
