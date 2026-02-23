import {
  Button,
  Flex,
  List,
  PageSpinner,
  Tag,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import NextLink from "next/link";
import { useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { getErrorMessage } from "~/features/common/helpers";
import { EDIT_SYSTEM_ROUTE } from "~/features/common/nav/routes";
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
import { isErrorResult } from "~/types/errors";

const { Paragraph, Text, Link: LinkText } = Typography;

const IntegrationLinkedSystems = ({
  connection,
}: {
  connection: MockConnection;
}) => {
  const messageApi = useMessage();
  const modalApi = useModal();
  const [isLinking, setIsLinking] = useState(false);

  const { data: systemLinksData, isLoading } = useGetSystemLinksQuery(
    connection.key,
    {
      skip: !connection.key,
    },
  );

  const [setSystemLinks] = useSetSystemLinksMutation();
  const [deleteSystemLink] = useDeleteSystemLinkMutation();

  const linkedSystems = systemLinksData || [];

  const handleConfirmUnlink = async (
    systemFidesKey: string,
    linkType: SystemConnectionLinkType,
  ) => {
    const result = await deleteSystemLink({
      connectionKey: connection.key,
      systemFidesKey,
      linkType,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success("System unlinked successfully");
    }
  };

  const handleUnlinkClicked = (
    systemFidesKey: string,
    linkType: SystemConnectionLinkType,
    systemName: string,
  ) => {
    modalApi.confirm({
      title: "Unlink system",
      content: (
        <div data-testid="unlink-system-modal">
          <Text type="secondary">
            Are you sure you want to unlink &ldquo;{systemName}&rdquo; from this
            integration? This action cannot be undone.
          </Text>
        </div>
      ),
      okText: "Unlink",
      okType: "danger",
      cancelText: "Cancel",
      onOk: () => handleConfirmUnlink(systemFidesKey, linkType),
    });
  };

  const handleLinkSystem = async (systemKey: string) => {
    if (!systemKey || !connection.key) {
      return;
    }

    const result = await setSystemLinks({
      connectionKey: connection.key,
      body: {
        links: [
          {
            system_fides_key: systemKey,
            link_type: "monitoring" as SystemConnectionLinkType,
          },
        ],
      },
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success("System linked successfully");
      setIsLinking(false);
    }
  };

  if (isLoading) {
    return (
      <div className="h-96">
        <PageSpinner />
      </div>
    );
  }

  return (
    <div>
      <div>
        <Typography.Title level={5}>Linked systems</Typography.Title>
        <Paragraph className="mt-2 w-2/3 text-gray-600">
          Link a system to automatically surface discovered assets and enable
          DSR execution within the system you manage.
        </Paragraph>
      </div>

      <div className="mb-4 flex items-center justify-end gap-2">
        {isLinking ? (
          <Flex gap="middle" align="flex-start" className="flex-1">
            {/* put this in a modal */}
            <SystemSelect
              onSelect={(value) => handleLinkSystem(value)}
              style={{ flex: 1 }}
              placeholder="Search for a system..."
            />
            <Button
              onClick={() => setIsLinking(false)}
              data-testid="cancel-link-system-button"
            >
              Cancel
            </Button>
          </Flex>
        ) : (
          <Button
            type="primary"
            onClick={() => setIsLinking(true)}
            data-testid="link-system-button"
            disabled={linkedSystems.length > 0}
          >
            Link system
          </Button>
        )}
      </div>

      <List
        dataSource={linkedSystems}
        data-testid="linked-systems-list"
        locale={{
          emptyText: (
            <div className="py-8 text-center">
              <Text type="secondary">
                No systems linked. Click &ldquo;Link system&rdquo; to add a
                system.
              </Text>
            </div>
          ),
        }}
        renderItem={(link: SystemLink) => (
          <List.Item
            key={`${link.system_fides_key}-${link.link_type}`}
            aria-label={`Linked system: ${link.system_name || link.system_fides_key} (${link.link_type})`}
            actions={[
              <Button
                key="unlink"
                type="link"
                onClick={() =>
                  handleUnlinkClicked(
                    link.system_fides_key,
                    link.link_type,
                    link.system_name || link.system_fides_key,
                  )
                }
                className="px-1"
                data-testid={`unlink-${link.system_fides_key}-${link.link_type}`}
                aria-label={`Unlink ${link.system_name || link.system_fides_key}`}
              >
                Unlink
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Flex gap={8} align="center" className="font-normal">
                  <div className="max-w-[300px]">
                    <NextLink
                      href={EDIT_SYSTEM_ROUTE.replace(
                        "[id]",
                        link.system_fides_key,
                      )}
                      passHref
                      legacyBehavior
                    >
                      <LinkText
                        variant="primary"
                        ellipsis
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Text
                          unStyled
                          ellipsis={{
                            tooltip: link.system_name || link.system_fides_key,
                          }}
                        >
                          {link.system_name || link.system_fides_key}
                        </Text>
                      </LinkText>
                    </NextLink>
                  </div>
                  <Tag>
                    {link.link_type === SystemConnectionLinkType.DSR
                      ? "Discovery"
                      : "Detection"}
                  </Tag>
                </Flex>
              }
            />
          </List.Item>
        )}
        className="mb-4"
      />
    </div>
  );
};

export default IntegrationLinkedSystems;
