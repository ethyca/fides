import {
  AntButton as Button,
  AntPagination as Pagination,
  Box,
  LinkIcon,
  TabList,
  Tabs,
  useDisclosure,
} from "fidesui";
import type { NextPage } from "next";
import React, { useMemo, useState } from "react";

import { FidesTab } from "~/features/common/DataTabs";
import { useFlags } from "~/features/common/features/features.slice";
import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import AddIntegrationModal from "~/features/integrations/add-integration/AddIntegrationModal";
import getIntegrationTypeInfo, {
  SUPPORTED_INTEGRATIONS,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import IntegrationList from "~/features/integrations/IntegrationList";
import SharedConfigModal from "~/features/integrations/SharedConfigModal";
import useIntegrationFilterTabs from "~/features/integrations/useIntegrationFilterTabs";

const DEFAULT_PAGE_SIZE = 50;
const MIN_ITEMS_FOR_PAGINATION = 10;

const IntegrationListView: NextPage = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  // DEFER (ENG-675): Remove this once the alpha feature is released
  const { flags } = useFlags();
  const supportedIntegrations = useMemo(() => {
    return SUPPORTED_INTEGRATIONS.filter((integration) => {
      return (
        integration !== "manual_webhook" || flags.alphaNewManualIntegration
      );
    });
  }, [flags.alphaNewManualIntegration]);

  const { data, isLoading } = useGetAllDatastoreConnectionsQuery({
    connection_type: supportedIntegrations,
    size: pageSize,
    page,
  });
  const { items, total } = data ?? {};

  const { onOpen, isOpen, onClose } = useDisclosure();
  const {
    tabIndex,
    onChangeFilter,
    anyFiltersApplied,
    isFiltering,
    filteredTypes,
    tabs,
  } = useIntegrationFilterTabs(
    items?.map((i) => getIntegrationTypeInfo(i.connection_type)),
  );

  const onChangeTabs = (newIndex: number) => {
    setPage(1);
    onChangeFilter(newIndex);
  };

  const integrations = useMemo(
    () =>
      items?.filter((integration) =>
        filteredTypes.some(
          (type) =>
            type.placeholder.connection_type === integration.connection_type,
        ),
      ) ?? [],
    [items, filteredTypes],
  );

  return (
    <Layout title="Integrations">
      <PageHeader
        heading="Integrations"
        breadcrumbItems={[
          {
            title: "All integrations",
          },
        ]}
      >
        <SharedConfigModal />
      </PageHeader>
      <Box data-testid="integration-tabs" display="flex">
        <Tabs index={tabIndex} onChange={onChangeTabs} w="full">
          <TabList>
            {tabs.map((label) => (
              <FidesTab label={label} key={label} />
            ))}
          </TabList>
        </Tabs>
        <Box
          borderBottom="2px solid"
          borderColor="gray.200"
          height="fit-content"
          pr="2"
          pb="2"
        >
          <Button
            onClick={onOpen}
            data-testid="add-integration-btn"
            icon={<LinkIcon />}
            iconPosition="end"
          >
            Add Integration
          </Button>
        </Box>
      </Box>
      {isLoading || isFiltering ? (
        <FidesSpinner />
      ) : (
        <>
          <IntegrationList
            integrations={integrations}
            onOpenAddModal={onOpen}
            isFiltered={anyFiltersApplied}
          />
          {!!total && total > MIN_ITEMS_FOR_PAGINATION && (
            <Pagination
              data-testid="pagination-controls"
              size="small"
              total={total}
              pageSize={pageSize}
              current={page}
              onChange={(pg, pgSize) => {
                setPage(pg);
                setPageSize(pgSize);
              }}
              showSizeChanger
            />
          )}
        </>
      )}
      <AddIntegrationModal isOpen={isOpen} onClose={onClose} />
    </Layout>
  );
};

export default IntegrationListView;
