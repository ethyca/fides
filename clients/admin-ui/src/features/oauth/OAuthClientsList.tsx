import { Flex, List, Pagination, Tag, Tooltip, Typography } from "fidesui";

import ClipboardButton from "~/features/common/ClipboardButton";
import { API_CLIENTS_ROUTE } from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { useHasPermission } from "~/features/common/Restrict";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { ClientResponse, ScopeRegistryEnum } from "~/types/api";

import { useListOAuthClientsQuery } from "./oauth-clients.slice";

const { Text } = Typography;

const ClientListItem = ({
  client,
  canUpdate,
}: {
  client: ClientResponse;
  canUpdate: boolean;
}) => {
  return (
    <List.Item data-testid={`client-list-item-${client.client_id}`}>
      <List.Item.Meta
        title={
          <Flex align="center" gap={8}>
            <Tooltip
              title={
                !canUpdate
                  ? "You don't have permission to edit API clients."
                  : undefined
              }
            >
              <span>
                <LinkCell
                  href={
                    canUpdate
                      ? `${API_CLIENTS_ROUTE}/${client.client_id}`
                      : undefined
                  }
                >
                  {client.name ?? "Unnamed"}
                </LinkCell>
              </span>
            </Tooltip>
            <Tag>{client.scopes.length} scopes</Tag>
          </Flex>
        }
        description={
          <Flex vertical gap={4}>
            <Flex align="center" gap={4}>
              <Text className="font-mono text-xs text-gray-400">
                {client.client_id}
              </Text>
              <ClipboardButton copyText={client.client_id} size="small" />
            </Flex>
            {client.description && (
              <Text className="text-sm text-gray-700">
                {client.description}
              </Text>
            )}
          </Flex>
        }
      />
    </List.Item>
  );
};

const OAuthClientsList = () => {
  const { paginationProps, pageIndex, pageSize } = useAntPagination();
  const { data, isLoading } = useListOAuthClientsQuery({
    page: pageIndex,
    size: pageSize,
  });
  const canUpdate = useHasPermission([ScopeRegistryEnum.CLIENT_UPDATE]);

  return (
    <Flex vertical>
      <List
        loading={isLoading}
        itemLayout="horizontal"
        dataSource={data?.items ?? []}
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
        renderItem={(client) => (
          <ClientListItem client={client} canUpdate={canUpdate} />
        )}
      />
      <Flex justify="end" className="mt-4">
        <Pagination
          {...paginationProps}
          total={data?.total ?? 0}
          showTotal={(totalItems) => `Total ${totalItems} items`}
        />
      </Flex>
    </Flex>
  );
};

export default OAuthClientsList;
