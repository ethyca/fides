import { Button, Flex, List, Tag, Typography } from "fidesui";
import NextLink from "next/link";
import { useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { EDIT_SYSTEM_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import {
  useDeleteSystemLinkMutation,
  useGetSystemLinksQuery,
  useSetSystemLinksMutation,
} from "~/features/integrations/system-links.slice";
import {
  MockConnection,
  SystemConnectionLinkType,
} from "~/mocks/system-links/data";

const { Link: LinkText } = Typography;

const IntegrationLinkedSystems = ({
  connection,
}: {
  connection: MockConnection;
}) => {
  const [isLinking, setIsLinking] = useState(false);
  const [selectedSystemKey, setSelectedSystemKey] = useState<
    string | undefined
  >(undefined);

  const { data: systemLinksData, isLoading } = useGetSystemLinksQuery(
    connection.key,
    {
      skip: !connection.key,
    },
  );

  const [setSystemLinks, { isLoading: isSettingLinks }] =
    useSetSystemLinksMutation();
  const [deleteSystemLink, { isLoading: isDeletingLink }] =
    useDeleteSystemLinkMutation();

  const linkedSystems = systemLinksData?.links || [];

  const handleLinkSystem = async () => {
    if (!selectedSystemKey || !connection.key) {
      return;
    }

    try {
      await setSystemLinks({
        connectionKey: connection.key,
        body: {
          links: [
            {
              system_fides_key: selectedSystemKey,
              link_type: "monitoring" as SystemConnectionLinkType,
            },
          ],
        },
      }).unwrap();
      setSelectedSystemKey(undefined);
      setIsLinking(false);
    } catch (error) {
      // Error handling can be added here
      // eslint-disable-next-line no-console
      console.error("Failed to link system:", error);
    }
  };

  const handleUnlink = async (
    systemFidesKey: string,
    linkType: SystemConnectionLinkType,
  ) => {
    if (!connection.key) {
      return;
    }

    try {
      await deleteSystemLink({
        connectionKey: connection.key,
        systemFidesKey,
        linkType,
      }).unwrap();
    } catch (error) {
      // Error handling can be added here
      // eslint-disable-next-line no-console
      console.error("Failed to unlink system:", error);
    }
  };

  if (isLoading) {
    return null;
  }

  return (
    <Flex vertical gap={2}>
      <Typography.Title level={5}>Linked systems</Typography.Title>
      {linkedSystems.length > 0 && (
        <List>
          {linkedSystems.map((system) => (
            <List.Item key={`${system.system_fides_key}-${system.link_type}`}>
              <Flex
                justify="space-between"
                align="center"
                style={{ width: "100%" }}
              >
                <Flex gap={2} flex={1}>
                  <NextLink
                    href={EDIT_SYSTEM_ROUTE.replace(
                      "[id]",
                      system.system_fides_key,
                    )}
                    passHref
                    legacyBehavior
                  >
                    <LinkText variant="primary" strong>
                      {system.system_name || system.system_fides_key}
                    </LinkText>
                  </NextLink>
                  <Tag>({system.link_type})</Tag>
                </Flex>
                <Restrict scopes={["system_integration_link:delete" as any]}>
                  <Button
                    type="link"
                    size="small"
                    onClick={() =>
                      handleUnlink(system.system_fides_key, system.link_type)
                    }
                    loading={isDeletingLink}
                    data-testid={`unlink-${system.system_fides_key}-${system.link_type}`}
                  >
                    Unlink
                  </Button>
                </Restrict>
              </Flex>
            </List.Item>
          ))}
        </List>
      )}
      {isLinking ? (
        <Flex gap={2} align="flex-start">
          <SystemSelect
            value={selectedSystemKey}
            onChange={(value) => setSelectedSystemKey(value as string)}
            style={{ flex: 1 }}
            placeholder="Search for a system..."
          />
          <Button
            type="primary"
            onClick={handleLinkSystem}
            loading={isSettingLinks}
            disabled={!selectedSystemKey}
          >
            Link
          </Button>
          <Button
            onClick={() => {
              setIsLinking(false);
              setSelectedSystemKey(undefined);
            }}
          >
            Cancel
          </Button>
        </Flex>
      ) : (
        <Button
          type="default"
          onClick={() => setIsLinking(true)}
          data-testid="link-system-button"
        >
          + Link system
        </Button>
      )}
    </Flex>
  );
};

export default IntegrationLinkedSystems;
