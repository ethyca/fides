import { Flex, List, Pagination, Tag, Typography } from "fidesui";
import { useState } from "react";

import { useHasPermission } from "~/features/common/Restrict";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { API_CLIENTS_ROUTE } from "~/features/common/nav/routes";
import { ClientResponse, ScopeRegistryEnum } from "~/types/api";

import { useListOAuthClientsQuery } from "./oauth-clients.slice";

const { Text } = Typography;

const ClientListItem = ({ client }: { client: ClientResponse }) => {
  const canUpdate = useHasPermission([ScopeRegistryEnum.CLIENT_UPDATE]);

  return (
    <List.Item data-testid={`client-list-item-${client.client_id}`}>
      <List.Item.Meta
        title={
          <Flex align="center" gap={8}>
            <LinkCell
              href={
                canUpdate
                  ? `${API_CLIENTS_ROUTE}/${client.client_id}`
                  : undefined
              }
            >
              {client.name ?? "Unnamed"}
            </LinkCell>
            <Tag>{client.scopes.length} scopes</Tag>
          </Flex>
        }
        description={
          <Flex vertical gap={2}>
            <Text type="secondary" className="font-mono text-xs">
              {client.client_id}
            </Text>
            {client.description && (
              <Text type="secondary">{client.description}</Text>
            )}
          </Flex>
        }
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
