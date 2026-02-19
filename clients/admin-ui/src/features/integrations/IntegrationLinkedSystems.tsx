import {
  Button,
  ColumnsType,
  Flex,
  Table,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { EDIT_SYSTEM_ROUTE } from "~/features/common/nav/routes";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import {
  useDeleteSystemLinkMutation,
  useGetSystemLinksQuery,
  useSetSystemLinksMutation,
} from "~/features/integrations/system-links.slice";
import {
  MockConnection,
  SystemConnectionLinkType,
  SystemLink,
} from "~/mocks/system-links/data";

const IntegrationLinkedSystems = ({
  connection,
}: {
  connection: MockConnection;
}) => {
  const messageApi = useMessage();
  const [isLinking, setIsLinking] = useState(false);

  const { data: systemLinksData, isLoading } = useGetSystemLinksQuery(
    connection.key,
    {
      skip: !connection.key,
    },
  );

  const [setSystemLinks] = useSetSystemLinksMutation();
  const [deleteSystemLink, { isLoading: isDeletingLink }] =
    useDeleteSystemLinkMutation();

  const linkedSystems = systemLinksData?.links || [];

  const handleUnlink = useCallback(
    async (systemFidesKey: string, linkType: SystemConnectionLinkType) => {
      if (!connection.key) {
        return;
      }

      try {
        await deleteSystemLink({
          connectionKey: connection.key,
          systemFidesKey,
          linkType,
        }).unwrap();
        messageApi.success("System unlinked successfully");
      } catch (error) {
        messageApi.error("Failed to unlink system");
      }
    },
    [connection.key, deleteSystemLink, messageApi],
  );

  const columns: ColumnsType<SystemLink> = useMemo(
    () => [
      {
        title: "System",
        dataIndex: "system_name",
        key: "system_name",
        render: (_: string, record: SystemLink) => (
          <LinkCell
            href={EDIT_SYSTEM_ROUTE.replace("[id]", record.system_fides_key)}
          >
            {record.system_name || record.system_fides_key}
          </LinkCell>
        ),
      },
      {
        title: "Link type",
        dataIndex: "link_type",
        key: "link_type",
        render: (linkType: SystemConnectionLinkType) => <Tag>({linkType})</Tag>,
      },
      {
        title: "Actions",
        key: "actions",
        render: (_: unknown, record: SystemLink) => (
          //   <Restrict scopes={["system_integration_link:delete" as any]}>
          <Button
            size="small"
            onClick={() =>
              handleUnlink(record.system_fides_key, record.link_type)
            }
            loading={isDeletingLink}
            data-testid={`unlink-${record.system_fides_key}-${record.link_type}`}
          >
            Unlink
          </Button>
          //   </Restrict>
        ),
      },
    ],
    [handleUnlink, isDeletingLink],
  );

  const handleLinkSystem = async (systemKey: string) => {
    if (!systemKey || !connection.key) {
      return;
    }

    try {
      await setSystemLinks({
        connectionKey: connection.key,
        body: {
          links: [
            {
              system_fides_key: systemKey,
              link_type: "monitoring" as SystemConnectionLinkType,
            },
          ],
        },
      }).unwrap();
      setIsLinking(false);
    } catch (error) {
      // Error handling can be added here
      // eslint-disable-next-line no-console
      console.error("Failed to link system:", error);
    }
  };

  if (isLoading) {
    return null;
  }

  return (
    <Flex vertical gap="middle">
      <Typography.Title level={5}>Linked systems</Typography.Title>
      {linkedSystems.length > 0 ? (
        <Table
          columns={columns}
          dataSource={linkedSystems}
          rowKey={(record) => `${record.system_fides_key}-${record.link_type}`}
          pagination={false}
          size="small"
          bordered
        />
      ) : null}
      {/* <Restrict scopes={["system_integration_link:create_or_update"]}> */}
      {isLinking ? (
        <Flex gap="middle" align="flex-start">
          <SystemSelect
            onSelect={(value) => handleLinkSystem(value)}
            style={{ flex: 1 }}
            placeholder="Search for a system..."
          />
        </Flex>
      ) : (
        <Flex>
          <Button
            type="default"
            onClick={() => setIsLinking(true)}
            data-testid="link-system-button"
          >
            + Link system
          </Button>
        </Flex>
      )}
      {/* </Restrict> */}
    </Flex>
  );
};

export default IntegrationLinkedSystems;
