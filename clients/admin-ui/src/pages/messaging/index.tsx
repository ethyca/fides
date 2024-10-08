/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  AntSwitch as Switch,
  Box,
  Flex,
  HStack,
  Link,
  Text,
  VStack,
} from "fidesui";
import { sortBy } from "lodash";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import InfoBox from "~/features/common/InfoBox";
import {
  MESSAGING_ADD_TEMPLATE_ROUTE,
  MESSAGING_EDIT_ROUTE,
} from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GroupCountBadgeCell,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { PaginationBar } from "~/features/common/table/v2/PaginationBar";
import AddMessagingTemplateModal from "~/features/messaging-templates/AddMessagingTemplateModal";
import { CustomizableMessagingTemplatesEnum } from "~/features/messaging-templates/CustomizableMessagingTemplatesEnum";
import CustomizableMessagingTemplatesLabelEnum from "~/features/messaging-templates/CustomizableMessagingTemplatesLabelEnum";
import { useGetSummaryMessagingTemplatesQuery } from "~/features/messaging-templates/messaging-templates.slice.plus";
import useMessagingTemplateToggle from "~/features/messaging-templates/useMessagingTemplateToggle";
import { useGetConfigurationSettingsQuery } from "~/features/privacy-requests";
import { useGetAllPropertiesQuery } from "~/features/properties";
import { MessagingTemplateWithPropertiesSummary } from "~/types/api";

const columnHelper =
  createColumnHelper<MessagingTemplateWithPropertiesSummary>();

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
  pages: 1,
};

const MessagingPage: NextPage = () => {
  const router = useRouter();
  const { toggleIsTemplateEnabled } = useMessagingTemplateToggle();

  const {
    PAGE_SIZES,
    pageSize,
    setPageSize,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    startRange,
    endRange,
    pageIndex,
    setTotalPages,
  } = useServerSidePagination();

  const {
    data: templateResponse,
    isLoading,
    isFetching,
  } = useGetSummaryMessagingTemplatesQuery({
    page: pageIndex,
    size: pageSize,
  });
  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => templateResponse ?? EMPTY_RESPONSE, [templateResponse]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const [isAddTemplateModalOpen, setIsAddTemplateModalOpen] =
    useState<boolean>(false);

  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.type, {
        id: "message",
        cell: (props) => (
          <DefaultCell
            value={
              CustomizableMessagingTemplatesLabelEnum[
                props.getValue() as CustomizableMessagingTemplatesEnum
              ]
            }
          />
        ),
        header: (props) => <DefaultHeaderCell value="Message" {...props} />,
        size: 150,
      }),

      columnHelper.accessor(
        (row) => (row.properties || []).map((property) => property.name),
        {
          id: "properties",
          cell: (props) => (
            <GroupCountBadgeCell
              suffix="properties"
              value={props.getValue()}
              {...props}
            />
          ),
          header: (props) => (
            <DefaultHeaderCell value="Properties" {...props} />
          ),
          meta: {
            displayText: "Properties",
            showHeaderMenu: true,
          },
          size: 250,
        },
      ),
      columnHelper.accessor((row) => row.is_enabled, {
        id: "is_enabled",
        cell: (props) => (
          <Flex align="center" justifyContent="flex-start" w="full" h="full">
            <Switch
              checked={props.getValue()}
              onChange={(v) => {
                toggleIsTemplateEnabled({
                  isEnabled: v,
                  templateId: props.row.original.id,
                });
              }}
            />
          </Flex>
        ),
        header: (props) => <DefaultHeaderCell value="Enable" {...props} />,
        size: 200,
        meta: {
          disableRowClick: true,
        },
      }),
    ],
    [toggleIsTemplateEnabled],
  );

  const sortedData = useMemo(() => sortBy(data, "id"), [data]);
  const tableInstance = useReactTable<MessagingTemplateWithPropertiesSummary>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: sortedData,
    columnResizeMode: "onChange",
  });

  return (
    <FixedLayout
      title="Messaging"
      mainProps={{
        padding: "0 40px 10px",
      }}
    >
      <PageHeader breadcrumbs={[{ title: "Messaging" }]}>
        <Text fontWeight={500} color="gray.700">
          Configure Fides messaging.
        </Text>
      </PageHeader>

      <FeatureNotEnabledInfoBox />
      <MissingMessagesInfoBox />

      <TableActionBar>
        <HStack alignItems="center" spacing={4} marginLeft="auto">
          <Button
            size="small"
            type="primary"
            data-testid="add-message-btn"
            onClick={() => setIsAddTemplateModalOpen(true)}
          >
            Add message +
          </Button>
        </HStack>
      </TableActionBar>

      {isLoading ? (
        <TableSkeletonLoader rowHeight={36} numRows={15} />
      ) : (
        <FidesTableV2
          tableInstance={tableInstance}
          onRowClick={(template) => {
            router.push({
              pathname: MESSAGING_EDIT_ROUTE,
              query: { id: template.id },
            });
          }}
          emptyTableNotice={<EmptyTableNotice />}
        />
      )}
      <PaginationBar
        totalRows={totalRows || 0}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isFetching}
        startRange={startRange}
        endRange={endRange}
      />

      <AddMessagingTemplateModal
        isOpen={isAddTemplateModalOpen}
        onClose={() => setIsAddTemplateModalOpen(false)}
        onAccept={(messageTemplateType) => {
          router.push({
            pathname: MESSAGING_ADD_TEMPLATE_ROUTE,
            query: { templateType: messageTemplateType },
          });
        }}
      />
    </FixedLayout>
  );
};

const EmptyTableNotice = () => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="no-results-notice"
    alignSelf="center"
    margin="auto"
    textAlign="center"
  >
    <VStack>
      <Text fontSize="md" fontWeight="600">
        It looks like it’s your first time here!
      </Text>
      <Text fontSize="sm">
        Add new email templates with the {`"Add message +"`} button.
        <br />
      </Text>
    </VStack>
  </VStack>
);

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
    <Box mb={6} data-testid="notice-properties-without-messaging-templates">
      <InfoBox
        title="Not all properties have messages configured."
        text={
          <Text as="span">
            You have properties that do not have messages configured. Users who
            submit privacy requests for these properties may not receive the
            necessary emails regarding their requests.{" "}
            <Box as="span">
              <QuestionTooltip
                label={propertiesWithoutMessagingTemplates
                  ?.map((p) => p.name)
                  .join(", ")}
              />
            </Box>
          </Text>
        }
        onClose={onDismissMessage}
      />
    </Box>
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
    <Box mb={6} data-testid="notice-properties-without-messaging-templates">
      <InfoBox
        title="Basic messaging enabled"
        text={
          <Text as="span">
            In basic messaging mode, you can edit the content of your messages
            from this screen. Please note that in basic messaging, the “Enable”
            toggle does not apply. Fides also supports property specific
            messaging mode. Read our{" "}
            <Link
              href="https://fid.es/property-specific-messaging"
              target="_blank"
              rel="nofollow"
              textDecoration="underline"
            >
              docs
            </Link>{" "}
            for more information about property specific mode or contact{" "}
            <Link href="mailto:support@ethyca.com" textDecoration="underline">
              Ethyca support
            </Link>{" "}
            to enable this mode on your Fides instance.
          </Text>
        }
      />
    </Box>
  );
};

export default MessagingPage;
