/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Button, HStack, Switch, Text, VStack } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import DataTabsHeader from "~/features/common/DataTabsHeader";
import FixedLayout from "~/features/common/FixedLayout";
import { MESSAGING_ADD_TEMPLATE_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import AddMessagingTemplateModal from "~/features/messaging-templates/AddMessagingTemplateModal";
import { useGetSummaryMessagingTemplatesQuery } from "~/features/messaging-templates/messaging-templates.slice";
import MessagingActionTypeLabelEnum from "~/features/messaging-templates/MessagingActionTypeLabelEnum";
import {
  MessagingActionType,
  MessagingTemplateWithPropertiesSummary,
} from "~/types/api";

const columnHelper =
  createColumnHelper<MessagingTemplateWithPropertiesSummary>();

const MessagingPage: NextPage = () => {
  const { data, isLoading } = useGetSummaryMessagingTemplatesQuery();
  const [isAddTemplateModalOpen, setIsAddTemplateModalOpen] =
    useState<boolean>(false);

  const router = useRouter();

  const emailTemplates = data?.items || [];

  console.log("data", emailTemplates);

  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.type, {
        id: "message",
        cell: (props) => (
          <DefaultCell
            value={
              MessagingActionTypeLabelEnum[
                props.getValue() as MessagingActionType
              ]
            }
          />
        ),
        header: (props) => <DefaultHeaderCell value="Message" {...props} />,
        size: 150,
      }),
      columnHelper.accessor((row) => row.properties, {
        id: "properties",
        cell: (props) => <span>Properties</span>,
        header: (props) => <DefaultHeaderCell value="Properties" {...props} />,
        size: 250,
      }),
      columnHelper.accessor((row) => row.is_enabled, {
        id: "is_enabled",
        cell: (props) => (
          <Switch
            isChecked={props.getValue()}
            onChange={(e) => {
              console.log("asdasd", e.target.checked);
            }}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Enable" {...props} />,
        size: 200,
      }),
    ],
    []
  );

  const tableInstance = useReactTable<MessagingTemplateWithPropertiesSummary>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: emailTemplates,
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

      <DataTabsHeader
        data={[{ label: "Email templates" }]}
        borderBottomWidth={1}
      />

      <TableActionBar>
        <HStack alignItems="center" spacing={4} marginLeft="auto">
          <Button
            size="xs"
            colorScheme="primary"
            data-testid="add-privacy-notice-btn"
            onClick={() => setIsAddTemplateModalOpen(true)}
          >
            Add message +
          </Button>
        </HStack>
      </TableActionBar>

      {isLoading && <TableSkeletonLoader rowHeight={36} numRows={15} />}
      {!isLoading && (
        <FidesTableV2
          tableInstance={tableInstance}
          onRowClick={() => {}}
          emptyTableNotice={<EmptyTableNotice />}
          enableSorting
        />
      )}

      <AddMessagingTemplateModal
        isOpen={isAddTemplateModalOpen}
        onClose={() => setIsAddTemplateModalOpen(false)}
        onAccept={(messageTemplateId) => {
          router.push({
            pathname: MESSAGING_ADD_TEMPLATE_ROUTE,
            query: { templateType: messageTemplateId },
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
        Lorem ipsum dolor sit, amet consectetur adipisicing elit. Ut distinctio
        odio sunt accusantium iusto, expedita id atque sed optio cum possimus
        incidunt necessitatibus iste, totam nobis ipsam maiores saepe unde.
        <br />
      </Text>
    </VStack>
  </VStack>
);

export default MessagingPage;
