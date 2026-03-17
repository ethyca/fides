import { Button, Flex, List, Pagination, Typography } from "fidesui";
import NextLink from "next/link";
import { useState } from "react";

import { useHasPermission } from "~/features/common/Restrict";
import { API_CLIENTS_ROUTE } from "~/features/common/nav/routes";
import { ClientResponse, ScopeRegistryEnum } from "~/types/api";

import { useListOAuthClientsQuery } from "./oauth-clients.slice";

const ClientListItem = ({ client }: { client: ClientResponse }) => {
  const canUpdate = useHasPermission([ScopeRegistryEnum.CLIENT_UPDATE]);

  return (
    <List.Item
      data-testid={`client-list-item-${client.client_id}`}
      actions={
        canUpdate
          ? [
              <NextLink
                key="edit"
                href={`${API_CLIENTS_ROUTE}/${client.client_id}`}
                passHref
                legacyBehavior
              >
                <Button
                  type="link"
                  data-testid={`edit-client-btn-${client.client_id}`}
                  className="px-1"
                >
                  Edit
                </Button>
              </NextLink>,
            ]
          : []
      }
    >
      <List.Item.Meta
        title={client.name ?? <em>Unnamed</em>}
        description={client.description ?? undefined}
      />
    </List.Item>
  );
};

const useOAuthClientsList = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const { data, isLoading, error } = useListOAuthClientsQuery({
    page,
    size: pageSize,
  });

  return {
    data: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    error,
    page,
    pageSize,
    setPage,
    setPageSize,
  };
};

const OAuthClientsList = () => {
  const { data, total, isLoading, page, pageSize, setPage, setPageSize } =
    useOAuthClientsList();

  return (
    <div>
      <List
        loading={isLoading}
        itemLayout="horizontal"
        dataSource={data}
        rowKey={(client) => client.client_id}
        locale={{
          emptyText: (
            <div className="px-4 py-8 text-center">
              <Typography.Paragraph type="secondary">
                No API clients yet. Click &quot;Create API client&quot; to get
                started.
              </Typography.Paragraph>
            </div>
          ),
        }}
        renderItem={(client) => <ClientListItem client={client} />}
      />
      {total > pageSize && (
        <Flex justify="end" className="mt-4">
          <Pagination
            current={page}
            total={total}
            pageSize={pageSize}
            onChange={(newPage, newPageSize) => {
              setPage(newPage);
              if (newPageSize !== pageSize) {
                setPageSize(newPageSize);
              }
            }}
            showSizeChanger
            showTotal={(totalItems) => `Total ${totalItems} items`}
          />
        </Flex>
      )}
    </div>
  );
};

export default OAuthClientsList;
