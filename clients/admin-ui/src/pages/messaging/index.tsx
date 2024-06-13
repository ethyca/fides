/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Spinner, Text, VStack } from "fidesui";
import { NextPage } from "next";
import { useMemo } from "react";

import DataTabsHeader from "~/features/common/DataTabsHeader";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
} from "~/features/common/table/v2";
import {
  MessagingTemplate,
  useGetMessagingTemplatesQuery,
} from "~/features/messaging-templates/messaging-templates.slice";

const columnHelper = createColumnHelper<MessagingTemplate>();

const MessagingPage: NextPage = () => {
  const { data: emailTemplates, isLoading } = useGetMessagingTemplatesQuery();

  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.label, {
        id: "message",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Message" {...props} />,
      }),
      columnHelper.accessor((row) => row.properties, {
        id: "properties",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Properties" {...props} />,
      }),
      columnHelper.accessor((row) => row.isEnabled, {
        id: "isEnabled",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Enable" {...props} />,
      }),
    ],
    []
  );

  const tableInstance = useReactTable<CustomFieldDefinitionWithId>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: emailTemplates || [],
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

      {isLoading && <Spinner />}
      {!isLoading && (
        <FidesTableV2
          tableInstance={tableInstance}
          onRowClick={() => {}}
          emptyTableNotice={<EmptyTableNotice />}
          enableSorting
        />
      )}
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
