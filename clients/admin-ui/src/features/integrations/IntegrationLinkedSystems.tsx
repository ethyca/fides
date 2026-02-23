import {
  Button,
  Flex,
  List,
  PageSpinner,
  Tag,
  Typography,
  useChakraDisclosure as useDisclosure,
  useMessage,
  WarningIcon,
} from "fidesui";
import NextLink from "next/link";
import { useCallback, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
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

const { Paragraph, Text, Link: LinkText } = Typography;

const IntegrationLinkedSystems = ({
  connection,
}: {
  connection: MockConnection;
}) => {
  const messageApi = useMessage();
  const [isLinking, setIsLinking] = useState(false);
  const [linkToDelete, setLinkToDelete] = useState<{
    systemFidesKey: string;
    linkType: SystemConnectionLinkType;
    systemName: string;
  } | null>(null);

  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const { data: systemLinksData, isLoading } = useGetSystemLinksQuery(
    connection.key,
    {
      skip: !connection.key,
    },
  );

  const [setSystemLinks] = useSetSystemLinksMutation();
  const [deleteSystemLink, { isLoading: isDeletingLink }] =
    useDeleteSystemLinkMutation();

  const linkedSystems = systemLinksData || [];

  const handleUnlink = useCallback(
    (
      systemFidesKey: string,
      linkType: SystemConnectionLinkType,
      systemName: string,
    ) => {
      setLinkToDelete({ systemFidesKey, linkType, systemName });
      onDeleteOpen();
    },
    [onDeleteOpen],
  );

  const handleConfirmUnlink = useCallback(async () => {
    if (!linkToDelete || !connection.key) {
      return;
    }

    try {
      await deleteSystemLink({
        connectionKey: connection.key,
        systemFidesKey: linkToDelete.systemFidesKey,
        linkType: linkToDelete.linkType,
      }).unwrap();
      messageApi.success("System unlinked successfully");
      setLinkToDelete(null);
    } catch (unlinkError) {
      messageApi.error("Failed to unlink system");
    }
    onDeleteClose();
  }, [
    linkToDelete,
    connection.key,
    deleteSystemLink,
    messageApi,
    onDeleteClose,
  ]);

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
      messageApi.success("System linked successfully");
      setIsLinking(false);
    } catch (linkError) {
      messageApi.error("Failed to link system");
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
          <Flex gap="middle" align="flex-start" style={{ flex: 1 }}>
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
                  handleUnlink(
                    link.system_fides_key,
                    link.link_type,
                    link.system_name || link.system_fides_key,
                  )
                }
                data-testid={`unlink-${link.system_fides_key}-${link.link_type}`}
                className="px-1"
                aria-label={`Unlink ${link.system_name || link.system_fides_key}`}
                loading={isDeletingLink}
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
                      ? "DSR"
                      : "Monitoring"}
                  </Tag>
                </Flex>
              }
            />
          </List.Item>
        )}
        className="mb-4"
      />

      <ConfirmationModal
        isOpen={isDeleteOpen}
        onClose={() => {
          setLinkToDelete(null);
          onDeleteClose();
        }}
        onConfirm={handleConfirmUnlink}
        title="Unlink system"
        data-testid="unlink-system-modal"
        message={
          <Text className="text-gray-500">
            Are you sure you want to unlink &ldquo;
            {linkToDelete?.systemName}&rdquo;? This action cannot be undone.
          </Text>
        }
        continueButtonText="Unlink"
        isCentered
        icon={<WarningIcon />}
        isLoading={isDeletingLink}
      />
    </div>
  );
};

export default IntegrationLinkedSystems;
