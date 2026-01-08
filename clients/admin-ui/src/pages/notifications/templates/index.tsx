import {
  Button,
  ColumnsType,
  Empty,
  Flex,
  Skeleton,
  Switch,
  Table,
  Typography,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import InfoBox from "~/features/common/InfoBox";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import { NOTIFICATIONS_ADD_TEMPLATE_ROUTE } from "~/features/common/nav/routes";
import NotificationTabs from "~/features/common/NotificationTabs";
import PageHeader from "~/features/common/PageHeader";
import { TagExpandableCell } from "~/features/common/table/cells/TagExpandableCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import { buildExpandCollapseMenu } from "~/features/data-discovery-and-detection/action-center/utils/columnBuilders";
import AddMessagingTemplateModal from "~/features/messaging-templates/AddMessagingTemplateModal";
import { useGetSummaryMessagingTemplatesQuery } from "~/features/messaging-templates/messaging-templates.slice.plus";
import useMessagingTemplateToggle from "~/features/messaging-templates/useMessagingTemplateToggle";
import { useGetAllPropertiesQuery } from "~/features/properties";
import { MessagingTemplateWithPropertiesSummary } from "~/types/api";

const MissingMessagesInfoBox = () => {
  /**
   * Fetch properties to check if there are any properties without messages configured.
   * If there are, show a notice to the user.
   */
  const MAX_PAGE_SIZE = 100; // Fetch the first 100 properties (max amount due to paging)
  const { isLoading: isLoadingProperties, data: properties } =
    useGetAllPropertiesQuery({
      page: 1,
      size: MAX_PAGE_SIZE,
    });
  const propertiesWithoutMessagingTemplates = properties?.items.filter(
    (p) => !p.messaging_templates || p.messaging_templates.length === 0,
  );
  const hasPropertiesWithoutMessagingTemplates = Boolean(
    !isLoadingProperties && propertiesWithoutMessagingTemplates?.length,
  );

  // Create a unique id for the current notice, so that we can save it if the user dismisses the notice
  // When the message changes, the ids will change, and the notice will be shown again
  const missingMessageNoticeId = `missing-messages-notice-${propertiesWithoutMessagingTemplates
    ?.map((p) => p.id)
    .join("-")}`;

  const [dismissedMessageNoticeId, setDismissedMessageNoticeId] =
    useLocalStorage<string>("notices.dismissedMessageNoticeId", "");
  const isDismissedMessage =
    missingMessageNoticeId === dismissedMessageNoticeId;

  const onDismissMessage = () => {
    setDismissedMessageNoticeId(missingMessageNoticeId);
  };

  // Show the notice if there are properties without messaging templates and the notice has not been dismissed
  const showMissingMessagesNotices =
    hasPropertiesWithoutMessagingTemplates && !isDismissedMessage;

  if (!showMissingMessagesNotices) {
    return null;
  }

  return (
    <InfoBox
      title="Not all properties have messages configured"
      text={
        <Typography.Text>
          You have properties that do not have messages configured. Users who
          submit privacy requests for these properties may not receive the
          necessary emails regarding their requests.{" "}
          <InfoTooltip
            label={propertiesWithoutMessagingTemplates
              ?.map((p) => p.name)
              .join(", ")}
          />
        </Typography.Text>
      }
      onClose={onDismissMessage}
      data-testid="notice-properties-without-messaging-templates"
    />
  );
};

const FeatureNotEnabledInfoBox = () => {
  const { data: appConfig } = useGetConfigurationSettingsQuery({
    api_set: false,
  });

  if (appConfig?.notifications.enable_property_specific_messaging) {
    return null;
  }

  return (
    <Flex data-testid="notice-properties-without-messaging-templates">
      <InfoBox
        title="Basic messaging enabled"
        text={
          <Typography.Text>
            In basic messaging mode, you can edit the content of your messages
            from this screen. Please note that in basic messaging, the
            &quot;Enable&quot; toggle does not apply. Fides also supports
            property specific messaging mode. Read our{" "}
            <Typography.Link
              href="https://fid.es/property-specific-messaging"
              target="_blank"
              rel="nofollow"
            >
              docs
            </Typography.Link>{" "}
            for more information about property specific mode or contact{" "}
            <Typography.Link href="mailto:support@ethyca.com">
              Ethyca support
            </Typography.Link>{" "}
            to enable this mode on your Fides instance.
          </Typography.Text>
        }
      />
    </Flex>
  );
};

const NotificationTemplatesPage: NextPage = () => {
  const router = useRouter();
  const { toggleIsTemplateEnabled } = useMessagingTemplateToggle();

  const tableState = useTableState({
    pagination: {
      defaultPageSize: 25,
      pageSizeOptions: [25, 50, 100],
    },
  });
  const [isPropertiesExpanded, setIsPropertiesExpanded] = useState(false);
  const [propertiesVersion, setPropertiesVersion] = useState(0);

  const [isAddTemplateModalOpen, setIsAddTemplateModalOpen] =
    useState<boolean>(false);

  const { pageIndex, pageSize } = tableState;

  const { data, isLoading, isFetching } = useGetSummaryMessagingTemplatesQuery({
    page: pageIndex,
    size: pageSize,
  });

  const columns: ColumnsType<MessagingTemplateWithPropertiesSummary> = useMemo(
    () => [
      {
        title: "Message",
        dataIndex: "type",
        key: "type",
      },
      {
        title: "Properties",
        dataIndex: "properties",
        key: "properties",
        render: (_, { properties }) => (
          <TagExpandableCell
            values={properties?.map((p) => ({
              label: p.name,
              key: p.id,
            }))}
            columnState={{
              isExpanded: isPropertiesExpanded,
              version: propertiesVersion,
            }}
          />
        ),
        menu: buildExpandCollapseMenu(
          setIsPropertiesExpanded,
          setPropertiesVersion,
        ),
      },
      {
        title: "Enable",
        dataIndex: "is_enabled",
        key: "is_enabled",
        render: (_, { is_enabled, id }) => (
          <Switch
            checked={is_enabled}
            onChange={(v) => {
              toggleIsTemplateEnabled({
                isEnabled: v,
                templateId: id,
              });
            }}
          />
        ),
      },
    ],
    [isPropertiesExpanded, propertiesVersion, toggleIsTemplateEnabled],
  );

  const { tableProps } = useAntTable(tableState, {
    dataSource: data?.items ?? [],
    totalRows: data?.total ?? 0,
    isLoading,
    isFetching,
    customTableProps: {
      locale: {
        emptyText: (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Flex vertical gap="small">
                <Typography.Text>No messages found</Typography.Text>
                <Button
                  type="primary"
                  onClick={() => setIsAddTemplateModalOpen(true)}
                >
                  Add message
                </Button>
              </Flex>
            }
          />
        ),
      },
    },
  });

  return (
    <FixedLayout title="Notifications">
      <PageHeader heading="Notifications" />

      <NotificationTabs />

      <Flex vertical gap="small" className="py-2">
        <FeatureNotEnabledInfoBox />
        <MissingMessagesInfoBox />
      </Flex>
      <Flex vertical gap="small">
        <Flex justify="flex-end">
          <Button
            type="primary"
            data-testid="add-message-btn"
            onClick={() => setIsAddTemplateModalOpen(true)}
          >
            Add message +
          </Button>
        </Flex>
        {isLoading ? (
          <Skeleton active />
        ) : (
          <Table {...tableProps} columns={columns} />
        )}
      </Flex>

      <AddMessagingTemplateModal
        isOpen={isAddTemplateModalOpen}
        onClose={() => setIsAddTemplateModalOpen(false)}
        onAccept={(messageTemplateType) => {
          router.push({
            pathname: NOTIFICATIONS_ADD_TEMPLATE_ROUTE,
            query: { templateType: messageTemplateType },
          });
        }}
      />
    </FixedLayout>
  );
};

export default NotificationTemplatesPage;
