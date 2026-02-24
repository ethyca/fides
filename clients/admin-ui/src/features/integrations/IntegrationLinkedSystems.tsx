import {
  Button,
  Flex,
  Input,
  List,
  Modal,
  PageSpinner,
  Tag,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import NextLink from "next/link";
import { useCallback, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { EDIT_SYSTEM_ROUTE } from "~/features/common/nav/routes";
import { debounce } from "~/features/common/utils";
import {
  SystemLinkResponse,
  useDeleteSystemLinkMutation,
  useGetSystemLinksQuery,
  useSetSystemLinksMutation,
} from "~/features/integrations/system-links.slice";
import { useGetSystemsQuery } from "~/features/system/system.slice";
import {
  BasicSystemResponseExtended,
  ConnectionConfigurationResponse,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const { Paragraph, Text, Link: LinkText } = Typography;

const SYSTEMS_PAGE_SIZE = 25;

const IntegrationLinkedSystems = ({
  connection,
}: {
  connection: ConnectionConfigurationResponse;
}) => {
  const messageApi = useMessage();
  const modalApi = useModal();
  const [linkSystemModalOpen, setLinkSystemModalOpen] = useState(false);
  const [searchInputValue, setSearchInputValue] = useState("");
  const [systemSearchValue, setSystemSearchValue] = useState("");

  const { data: linkedSystems, isLoading } = useGetSystemLinksQuery(
    connection.key,
    {
      skip: !connection.key,
    },
  );

  const [setSystemLinks] = useSetSystemLinksMutation();
  const [deleteSystemLink] = useDeleteSystemLinkMutation();

  const { data: systemsPage, isFetching: isSystemsLoading } =
    useGetSystemsQuery(
      {
        page: 1,
        size: SYSTEMS_PAGE_SIZE,
        search: systemSearchValue.length > 1 ? systemSearchValue : undefined,
      },
      { skip: !linkSystemModalOpen },
    );

  const linkedKeys = useMemo(
    () => new Set((linkedSystems ?? []).map((l) => l.system_fides_key)),
    [linkedSystems],
  );

  const availableSystems = useMemo(
    () =>
      (systemsPage?.items ?? []).filter((s) => !linkedKeys.has(s.fides_key)),
    [systemsPage?.items, linkedKeys],
  );

  const handleSystemSearch = useCallback((value: string) => {
    setSystemSearchValue(value ?? "");
  }, []);
  const debouncedSystemSearch = useMemo(
    () => debounce(handleSystemSearch, 300),
    [handleSystemSearch],
  );

  const handleConfirmUnlink = async (systemFidesKey: string) => {
    const result = await deleteSystemLink({
      connectionKey: connection.key,
      systemFidesKey,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success("System unlinked successfully");
    }
  };

  const handleUnlinkClicked = (systemFidesKey: string, systemName: string) => {
    modalApi.confirm({
      title: "Unlink system",
      content: (
        <Text type="secondary">
          Are you sure you want to unlink &ldquo;{systemName}&rdquo; from this
          integration? This action cannot be undone.
        </Text>
      ),
      okText: "Unlink",
      okType: "danger",
      cancelText: "Cancel",
      onOk: () => handleConfirmUnlink(systemFidesKey),
      centered: true,
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
          },
        ],
      },
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success("System linked successfully");
      setLinkSystemModalOpen(false);
      setSearchInputValue("");
      setSystemSearchValue("");
    }
  };

  const openLinkModal = () => {
    setSearchInputValue("");
    setSystemSearchValue("");
    setLinkSystemModalOpen(true);
  };

  const closeLinkModal = () => {
    setLinkSystemModalOpen(false);
    setSearchInputValue("");
    setSystemSearchValue("");
  };

  if (isLoading) {
    return (
      <div className="h-96">
        <PageSpinner />
      </div>
    );
  }

  return (
    <Flex vertical gap="middle">
      <Typography.Title level={5}>Linked systems</Typography.Title>
      <Paragraph className="mt-2 w-2/3" type="secondary">
        Link a system to automatically surface discovered assets and enable DSR
        execution within the system you manage.
      </Paragraph>

      <Flex className="absolute right-2 top-2">
        <Button
          type="primary"
          onClick={openLinkModal}
          data-testid="link-system-button"
          disabled={!!linkedSystems?.length}
        >
          Link system
        </Button>
      </Flex>

      <Modal
        open={linkSystemModalOpen}
        onCancel={closeLinkModal}
        title="Link system"
        footer={
          <Button
            onClick={closeLinkModal}
            data-testid="cancel-link-system-button"
          >
            Cancel
          </Button>
        }
        width={520}
        data-testid="link-system-modal"
      >
        <Flex vertical gap="middle" className="max-h-96">
          <Typography.Text>Select a system to link</Typography.Text>
          <Input.Search
            placeholder="Search..."
            allowClear
            value={searchInputValue}
            onChange={({ target: { value } }) => {
              setSearchInputValue(value);
              debouncedSystemSearch(value);
            }}
            onSearch={(value) => {
              setSearchInputValue(value);
              debouncedSystemSearch(value);
            }}
            aria-label="Search systems"
            data-testid="link-system-search"
          />
          <List
            dataSource={availableSystems}
            loading={isSystemsLoading}
            locale={{
              emptyText: (
                <div className="py-6 text-center">
                  <Text type="secondary">
                    {systemSearchValue.length > 1
                      ? "No matching systems. Try a different search."
                      : "No systems available to link."}
                  </Text>
                </div>
              ),
            }}
            renderItem={(system: BasicSystemResponseExtended) => (
              <List.Item
                key={system.fides_key}
                aria-label={`Link system: ${system.name ?? system.fides_key}`}
                actions={[
                  <Button
                    key="link"
                    type="link"
                    onClick={() => handleLinkSystem(system.fides_key)}
                    data-testid={`link-system-option-${system.fides_key}`}
                    aria-label={`Link system: ${system.name ?? system.fides_key}`}
                  >
                    Link
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Text
                      ellipsis={{
                        tooltip: system.name ?? system.fides_key,
                      }}
                    >
                      {system.name ?? system.fides_key}
                    </Text>
                  }
                  description={
                    system.description ? (
                      <Text type="secondary">{system.description}</Text>
                    ) : undefined
                  }
                />
              </List.Item>
            )}
          />
        </Flex>
      </Modal>

      <List
        dataSource={linkedSystems || []}
        data-testid="linked-systems-list"
        locale={{
          emptyText: (
            <Flex className="w-full justify-center">
              <Text type="secondary">
                No systems linked. Click &ldquo;Link system&rdquo; to add a
                system.
              </Text>
            </Flex>
          ),
        }}
        renderItem={(link: SystemLinkResponse) => (
          <List.Item
            key={link.system_fides_key}
            aria-label={`Linked system: ${link.system_name || link.system_fides_key}`}
            actions={[
              <Button
                key="unlink"
                type="link"
                onClick={() =>
                  handleUnlinkClicked(
                    link.system_fides_key,
                    link.system_name || link.system_fides_key,
                  )
                }
                className="px-1"
                data-testid={`unlink-${link.system_fides_key}`}
                aria-label={`Unlink ${link.system_name || link.system_fides_key}`}
              >
                Unlink
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Flex gap={8} align="center" className="font-normal">
                  <Flex>
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
                  </Flex>
                  <Tag>Discovery</Tag>
                </Flex>
              }
            />
          </List.Item>
        )}
      />
    </Flex>
  );
};

export default IntegrationLinkedSystems;
