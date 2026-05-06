import {
  Button,
  Flex,
  Input,
  List,
  Modal,
  Spin,
  Switch,
  Tag,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RouterLink } from "~/features/common/nav/RouterLink";
import { DATASET_DETAIL_ROUTE } from "~/features/common/nav/routes";
import { debounce } from "~/features/common/utils";
import { useGetAllFilteredDatasetsQuery } from "~/features/dataset";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  usePatchDatastoreConnectionsMutation,
  usePutDatasetConfigsMutation,
} from "~/features/datastore-connections";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  SystemType,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const { Paragraph, Text } = Typography;

const IntegrationPrivacyRequests = ({
  connection,
  integrationOption,
}: {
  connection: ConnectionConfigurationResponse;
  integrationOption?: ConnectionSystemTypeMap;
}) => {
  const messageApi = useMessage();
  const modalApi = useModal();

  // -- Status (enable / disable for privacy requests) -----------------------

  const [patchConnection, { isLoading: isPatchingStatus }] =
    usePatchDatastoreConnectionsMutation();

  const enabled = !connection.disabled;

  const handleToggleEnabled = async (nextEnabled: boolean) => {
    const result = await patchConnection({
      key: connection.key,
      name: connection.name ?? connection.key,
      disabled: !nextEnabled,
      access: connection.access,
      connection_type: connection.connection_type,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success(
      nextEnabled
        ? "Integration enabled for privacy requests"
        : "Integration disabled for privacy requests",
    );
  };

  // -- Datasets (database integrations only) --------------------------------

  const supportsDatasets = integrationOption?.type === SystemType.DATABASE;

  const [linkModalOpen, setLinkModalOpen] = useState(false);
  const [searchInputValue, setSearchInputValue] = useState("");
  const [datasetSearchValue, setDatasetSearchValue] = useState("");

  const { data: linkedDatasetsPage, isLoading: isLoadingLinkedDatasets } =
    useGetConnectionConfigDatasetConfigsQuery(connection.key, {
      skip: !connection.key || !supportsDatasets,
    });

  const linkedDatasets = useMemo(
    () => linkedDatasetsPage?.items ?? [],
    [linkedDatasetsPage],
  );
  const linkedDatasetKeys = useMemo(
    () => linkedDatasets.map((d) => d.fides_key),
    [linkedDatasets],
  );

  const [putDatasetConfigs] = usePutDatasetConfigsMutation();

  // The dataset config endpoint replaces the entire linked set, so unlink and
  // link are both expressed as a PUT of the new desired key list.
  const writeLinkedDatasetKeys = useCallback(
    (nextKeys: string[]) =>
      putDatasetConfigs({
        connection_key: connection.key,
        dataset_pairs: nextKeys.map((fides_key) => ({
          fides_key,
          ctl_dataset_fides_key: fides_key,
        })),
      }),
    [connection.key, putDatasetConfigs],
  );

  const { data: unlinkedDatasets, isFetching: isUnlinkedFetching } =
    useGetAllFilteredDatasetsQuery(
      {
        onlyUnlinkedDatasets: true,
        minimal: true,
      },
      { skip: !linkModalOpen },
    );

  const filteredUnlinkedDatasets = useMemo(() => {
    const term = datasetSearchValue.trim().toLowerCase();
    const list = unlinkedDatasets ?? [];
    if (!term) {
      return list;
    }
    return list.filter(
      (d) =>
        d.fides_key.toLowerCase().includes(term) ||
        (d.name ?? "").toLowerCase().includes(term),
    );
  }, [unlinkedDatasets, datasetSearchValue]);

  const handleDatasetSearch = useCallback((value: string) => {
    setDatasetSearchValue(value ?? "");
  }, []);
  const debouncedDatasetSearch = useMemo(
    () => debounce(handleDatasetSearch, 300),
    [handleDatasetSearch],
  );

  const closeLinkModal = () => {
    setLinkModalOpen(false);
    setSearchInputValue("");
    setDatasetSearchValue("");
  };

  const openLinkModal = () => {
    setSearchInputValue("");
    setDatasetSearchValue("");
    setLinkModalOpen(true);
  };

  const handleLinkDataset = async (datasetKey: string) => {
    if (!datasetKey || !connection.key) {
      return;
    }
    const result = await writeLinkedDatasetKeys([
      ...linkedDatasetKeys,
      datasetKey,
    ]);
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Dataset linked successfully");
    closeLinkModal();
  };

  const handleConfirmUnlink = async (datasetKey: string) => {
    const result = await writeLinkedDatasetKeys(
      linkedDatasetKeys.filter((k) => k !== datasetKey),
    );
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success("Dataset unlinked successfully");
    }
  };

  const handleUnlinkClicked = (datasetKey: string, datasetName: string) => {
    modalApi.confirm({
      title: "Unlink dataset",
      content: (
        <Text type="secondary">
          Are you sure you want to unlink &ldquo;{datasetName}&rdquo; from this
          integration? Privacy requests will no longer traverse this dataset via
          this integration.
        </Text>
      ),
      okText: "Unlink",
      okType: "danger",
      cancelText: "Cancel",
      onOk: () => handleConfirmUnlink(datasetKey),
      centered: true,
    });
  };

  // -------------------------------------------------------------------------

  return (
    <Flex vertical gap="large">
      <Flex vertical gap="small">
        <Typography.Title level={5}>Status</Typography.Title>
        <Flex align="center" gap="middle">
          <Switch
            checked={enabled}
            onChange={handleToggleEnabled}
            loading={isPatchingStatus}
            data-testid="toggle-enabled"
          />
          <Text>Enable for privacy requests</Text>
        </Flex>
        <Paragraph type="secondary" className="m-0">
          When enabled, this integration is used during privacy request
          execution.
        </Paragraph>
      </Flex>

      {supportsDatasets && (
        <Flex vertical gap="small">
          <Flex justify="space-between" align="center">
            <Typography.Title level={5} className="m-0">
              Datasets
            </Typography.Title>
            <Button
              type="primary"
              onClick={openLinkModal}
              data-testid="link-dataset-button"
            >
              Link dataset
            </Button>
          </Flex>
          <Paragraph type="secondary" className="m-0">
            Datasets associated with this integration are used to traverse and
            fulfill privacy requests.
          </Paragraph>

          <Modal
            open={linkModalOpen}
            onCancel={closeLinkModal}
            title="Link dataset"
            footer={
              <Button
                onClick={closeLinkModal}
                data-testid="cancel-link-dataset-button"
              >
                Cancel
              </Button>
            }
            width={520}
            wrapProps={{ "data-testid": "link-dataset-modal" }}
          >
            <Flex vertical gap="medium" className="max-h-96">
              <Input.Search
                placeholder="Search..."
                allowClear
                value={searchInputValue}
                onChange={({ target: { value } }) => {
                  setSearchInputValue(value);
                  debouncedDatasetSearch(value);
                }}
                onSearch={(value) => {
                  setSearchInputValue(value);
                  debouncedDatasetSearch(value);
                }}
                aria-label="Search datasets"
                data-testid="link-dataset-search"
              />
              <List
                dataSource={filteredUnlinkedDatasets}
                loading={isUnlinkedFetching}
                locale={{
                  emptyText: (
                    <div className="py-6 text-center">
                      <Text type="secondary">
                        {datasetSearchValue.length > 0
                          ? "No matching datasets. Try a different search."
                          : "No datasets available to link."}
                      </Text>
                    </div>
                  ),
                }}
                renderItem={(dataset) => {
                  const displayName = dataset.name ?? dataset.fides_key;
                  const showFidesKey = displayName !== dataset.fides_key;
                  return (
                    <List.Item
                      key={dataset.fides_key}
                      actions={[
                        <Button
                          key="link"
                          type="link"
                          size="small"
                          onClick={() => handleLinkDataset(dataset.fides_key)}
                          data-testid={`link-dataset-option-${dataset.fides_key}`}
                          aria-label={`Link dataset: ${displayName}`}
                        >
                          Link
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <Flex align="center" gap={8} className="w-full">
                            <Text
                              className="min-w-0 flex-1 truncate"
                              ellipsis={{ tooltip: displayName }}
                            >
                              {displayName}
                            </Text>
                            {showFidesKey && (
                              <Tag className="max-w-72 shrink-0 truncate font-mono text-xs">
                                {dataset.fides_key}
                              </Tag>
                            )}
                          </Flex>
                        }
                        description={dataset.description ?? undefined}
                      />
                    </List.Item>
                  );
                }}
                className="overflow-y-auto"
              />
            </Flex>
          </Modal>

          {isLoadingLinkedDatasets ? (
            <div className="h-32">
              <Spin />
            </div>
          ) : (
            <List
              dataSource={linkedDatasets}
              data-testid="linked-datasets-list"
              locale={{
                emptyText: (
                  <Flex className="w-full justify-center">
                    <Text
                      type="secondary"
                      data-testid="no-datasets-linked-text"
                    >
                      No datasets linked. Click &ldquo;Link dataset&rdquo; to
                      add a dataset.
                    </Text>
                  </Flex>
                ),
              }}
              renderItem={(datasetConfig) => {
                const datasetName =
                  datasetConfig.ctl_dataset?.name || datasetConfig.fides_key;
                const showFidesKey = datasetName !== datasetConfig.fides_key;
                return (
                  <List.Item
                    key={datasetConfig.fides_key}
                    aria-label={`Linked dataset: ${datasetName}`}
                    actions={[
                      <Button
                        key="unlink"
                        type="link"
                        onClick={() =>
                          handleUnlinkClicked(
                            datasetConfig.fides_key,
                            datasetName,
                          )
                        }
                        className="px-1"
                        data-testid={`unlink-dataset-${datasetConfig.fides_key}`}
                        aria-label={`Unlink ${datasetName}`}
                      >
                        Unlink
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Flex
                          gap={8}
                          align="center"
                          className="w-full font-normal"
                        >
                          <Flex className="min-w-0 flex-1">
                            <RouterLink
                              href={DATASET_DETAIL_ROUTE.replace(
                                "[datasetId]",
                                datasetConfig.fides_key,
                              )}
                              variant="primary"
                              ellipsis
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Text
                                unStyled
                                ellipsis={{
                                  tooltip: datasetName,
                                }}
                              >
                                {datasetName}
                              </Text>
                            </RouterLink>
                          </Flex>
                          {showFidesKey && (
                            <Tag className="max-w-72 shrink-0 truncate font-mono text-xs">
                              {datasetConfig.fides_key}
                            </Tag>
                          )}
                        </Flex>
                      }
                      description={
                        datasetConfig.ctl_dataset?.description ?? undefined
                      }
                    />
                  </List.Item>
                );
              }}
            />
          )}
        </Flex>
      )}
    </Flex>
  );
};

export default IntegrationPrivacyRequests;
