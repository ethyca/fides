/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Button, Flex, HStack, Switch, Text, VStack } from "fidesui";
import { sortBy } from "lodash";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import DataTabsHeader from "~/features/common/DataTabsHeader";
import FixedLayout from "~/features/common/FixedLayout";
import {
  MESSAGING_ADD_TEMPLATE_ROUTE,
  MESSAGING_EDIT_ROUTE,
} from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
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
import {
  useGetSummaryMessagingTemplatesQuery,
  usePatchMessagingTemplateByIdMutation,
} from "~/features/messaging-templates/messaging-templates.slice";
import MessagingActionTypeLabelEnum from "~/features/messaging-templates/MessagingActionTypeLabelEnum";
import {
  MessagingActionType,
  MessagingTemplateWithPropertiesSummary,
} from "~/types/api";

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

  const [patchMessagingTemplateById] = usePatchMessagingTemplateByIdMutation();

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

  const router = useRouter();

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
        }
      ),
      columnHelper.accessor((row) => row.is_enabled, {
        id: "is_enabled",
        cell: (props) => (
          <Flex align="center" justifyContent="flex-start" w="full" h="full">
            <Switch
              isChecked={props.getValue()}
              onChange={(e) => {
                patchMessagingTemplateById({
                  templateId: props.row.original.id,
                  template: { is_enabled: e.target.checked },
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
    []
  );

  const sortedData = sortBy(data, "id");
  const tableInstance = useReactTable<MessagingTemplateWithPropertiesSummary>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: sortedData,
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
        totalRows={totalRows}
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

export default MessagingPage;
