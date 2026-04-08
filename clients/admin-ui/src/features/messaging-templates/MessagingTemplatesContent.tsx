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
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import InfoBox from "~/features/common/InfoBox";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import {
  NOTIFICATIONS_ADD_TEMPLATE_ROUTE,
  NOTIFICATIONS_TEMPLATES_ROUTE,
} from "~/features/common/nav/routes";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { TagExpandableCell } from "~/features/common/table/cells/TagExpandableCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import { buildExpandCollapseMenu } from "~/features/data-discovery-and-detection/action-center/utils/columnBuilders";
import { useGetAllPropertiesQuery } from "~/features/properties";
import { MessagingTemplateWithPropertiesSummary } from "~/types/api";

import AddMessagingTemplateModal from "./AddMessagingTemplateModal";
import { CustomizableMessagingTemplatesEnum } from "./CustomizableMessagingTemplatesEnum";
import CustomizableMessagingTemplatesLabelEnum from "./CustomizableMessagingTemplatesLabelEnum";
import { useGetSummaryMessagingTemplatesQuery } from "./messaging-templates.slice.plus";
import useMessagingTemplateToggle from "./useMessagingTemplateToggle";

const MissingMessagesInfoBox = () => {
  const MAX_PAGE_SIZE = 100;
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

/**
 * Core messaging templates content without Layout/SidePanel wrappers.
 * Used by the Privacy Requests Configuration hub page and the standalone
 * Notifications Templates page.
 */
const MessagingTemplatesContent = () => {
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

  const { data, isLoading, isFetching, error } =
    useGetSummaryMessagingTemplatesQuery({
      page: pageIndex,
      size: pageSize,
    });

  const columns: ColumnsType<MessagingTemplateWithPropertiesSummary> = useMemo(
    () => [
      {
        title: "Message",
        dataIndex: "type",
        key: "type",
        render: (_, { type, id }) => {
          return (
            <LinkCell href={`${NOTIFICATIONS_TEMPLATES_ROUTE}/${id}`}>
              {
                CustomizableMessagingTemplatesLabelEnum[
                  type as CustomizableMessagingTemplatesEnum
                ]
              }
            </LinkCell>
          );
        },
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

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your messaging templates"
      />
    );
  }

  return (
    <>
      <Flex justify="end" className="mb-2">
        <Button
          type="primary"
          data-testid="add-message-btn"
          onClick={() => setIsAddTemplateModalOpen(true)}
        >
          Add message +
        </Button>
      </Flex>

      <Flex vertical gap="small" className="py-2">
        <FeatureNotEnabledInfoBox />
        <MissingMessagesInfoBox />
      </Flex>
      <Flex vertical gap="small">
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
    </>
  );
};

export default MessagingTemplatesContent;
