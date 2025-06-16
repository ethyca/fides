import {
  AntButton as Button,
  AntPagination as Pagination,
  AntTabs,
  Box,
  LinkIcon,
  useDisclosure,
} from "fidesui";
import type { NextPage } from "next";
import React, { useMemo, useState } from "react";

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
import { ConnectionType } from "~/types/api";

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
        integration !== ConnectionType.MANUAL_WEBHOOK ||
        flags.alphaNewManualIntegration
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
    activeKey,
    onChangeFilter,
    anyFiltersApplied,
    isUpdatingFilter,
    filteredTypes,
    tabItems,
  } = useIntegrationFilterTabs({
    integrationTypes: items?.map((i) =>
      getIntegrationTypeInfo(i.connection_type),
    ),
    useHashing: true,
  });

  const onChangeTabs = (newKey: string) => {
    setPage(1);
    onChangeFilter(newKey);
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
        <AntTabs
          activeKey={activeKey}
          onChange={onChangeTabs}
          items={tabItems}
          className="w-full"
          tabBarExtraContent={
            <Button
              onClick={onOpen}
              data-testid="add-integration-btn"
              icon={<LinkIcon />}
              iconPosition="end"
            >
              Add Integration
            </Button>
          }
        />
      </Box>
      {isLoading || isUpdatingFilter ? (
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
