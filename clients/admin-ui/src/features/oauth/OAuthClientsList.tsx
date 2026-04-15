import { Flex, List, Pagination, Tag, Tooltip, Typography } from "fidesui";

import { API_CLIENTS_ROUTE } from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { useHasPermission } from "~/features/common/Restrict";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { ClientResponse, ScopeRegistryEnum } from "~/types/api";

import { pluralize } from "../common/utils";
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
            <Tag>{client.scopes?.length ?? 0} scopes</Tag>
          </Flex>
        }
        description={
          <Flex vertical gap={4}>
            <Flex align="center" gap={4}>
              <Text className="font-mono text-xs" type="secondary" copyable>
                {client.client_id}
              </Text>
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
    <Flex vertical gap={8}>
      <List
        loading={isLoading}
        itemLayout="horizontal"
        dataSource={data?.items ?? []}
        rowKey="client_id"
        locale={{
          emptyText: (
            <Typography.Paragraph type="secondary">
              No API clients yet. Click &quot;Create API client&quot; to get
              started.
            </Typography.Paragraph>
          ),
        }}
        renderItem={(client) => (
          <ClientListItem client={client} canUpdate={canUpdate} />
        )}
      />
      <Flex justify="end">
        <Pagination
          {...paginationProps}
          total={data?.total ?? 0}
          showTotal={(totalItems) =>
            `Total ${pluralize(totalItems, "item", "items")}`
          }
        />
      </Flex>
    </Flex>
  );
};

export default OAuthClientsList;
