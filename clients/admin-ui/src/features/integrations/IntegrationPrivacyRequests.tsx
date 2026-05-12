import {
  Button,
  ColumnsType,
  Flex,
  Input,
  List,
  Modal,
  Spin,
  Switch,
  Table,
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
  Dataset,
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
  const [selectedDatasetKeys, setSelectedDatasetKeys] = useState<string[]>([]);
  const [isLinkingSelected, setIsLinkingSelected] = useState(false);
  // Track which row's unlink PUT is in flight so we can disable its button
  // (and gate the confirmation modal's OK) — without a guard, a double-click
  // races two concurrent PUTs that both overwrite the whole linked-key list.
  const [unlinkingKey, setUnlinkingKey] = useState<string | null>(null);

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
        (d.name ?? "").toLowerCase().includes(term) ||
        (d.description ?? "").toLowerCase().includes(term),
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
    setSelectedDatasetKeys([]);
  };

  const openLinkModal = () => {
    setSearchInputValue("");
    setDatasetSearchValue("");
    setSelectedDatasetKeys([]);
    setLinkModalOpen(true);
  };

  // PUT /connection/{key}/datasetconfig is a bulk endpoint: it returns 200 OK
  // even when individual entries fail validation, surfacing those failures in
  // the `failed` array of the response body. Treat any non-empty `failed` as
  // a user-facing error and bail before showing a success toast — leaving the
  // modal open so the user can adjust their selection and retry.
  const handleLinkSelected = async () => {
    if (!connection.key || selectedDatasetKeys.length === 0) {
      return;
    }
    setIsLinkingSelected(true);
    try {
      const result = await writeLinkedDatasetKeys([
        ...linkedDatasetKeys,
        ...selectedDatasetKeys,
      ]);
      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
        return;
      }
      const firstFailure = result.data?.failed?.[0];
      if (firstFailure) {
        messageApi.error(firstFailure.message);
        return;
      }
      messageApi.success(
        selectedDatasetKeys.length === 1
          ? "Dataset linked successfully"
          : `${selectedDatasetKeys.length} datasets linked successfully`,
      );
      closeLinkModal();
    } finally {
      setIsLinkingSelected(false);
    }
  };

  const handleConfirmUnlink = async (datasetKey: string) => {
    setUnlinkingKey(datasetKey);
    try {
      const result = await writeLinkedDatasetKeys(
        linkedDatasetKeys.filter((k) => k !== datasetKey),
      );
      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
        return;
      }
      const firstFailure = result.data?.failed?.[0];
      if (firstFailure) {
        messageApi.error(firstFailure.message);
        return;
      }
      messageApi.success("Dataset unlinked successfully");
    } finally {
      setUnlinkingKey(null);
    }
  };

  const handleUnlinkClicked = (datasetKey: string, datasetName: string) => {
    if (unlinkingKey) {
      return;
    }
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

  const linkDatasetColumns: ColumnsType<Dataset> = useMemo(
    () => [
      {
        title: "Dataset",
        dataIndex: "name",
        key: "name",
        ellipsis: { showTitle: false },
        render: (name: string | null | undefined, row: Dataset) => {
          const display = name ?? row.fides_key;
          return (
            <Text strong ellipsis={{ tooltip: display }}>
              {display}
            </Text>
          );
        },
      },
      {
        title: "Fides key",
        dataIndex: "fides_key",
        key: "fides_key",
        ellipsis: { showTitle: false },
        render: (fidesKey: string) => (
          <Text
            type="secondary"
            className="font-mono text-xs"
            ellipsis={{ tooltip: fidesKey }}
          >
            {fidesKey}
          </Text>
        ),
      },
      {
        title: "Description",
        dataIndex: "description",
        key: "description",
        ellipsis: { showTitle: false },
        render: (description: string | null | undefined) =>
          description ? (
            <Text type="secondary" ellipsis={{ tooltip: description }}>
              {description}
            </Text>
          ) : (
            <Text type="secondary">—</Text>
          ),
      },
    ],
    [],
  );

  // -------------------------------------------------------------------------

  return (
    <Flex vertical gap="large">
      <Flex vertical gap="small">
        <Typography.Title level={5}>
          Privacy request automation
        </Typography.Title>
        <Flex align="center" gap="middle">
          <Switch
            checked={enabled}
            onChange={handleToggleEnabled}
            loading={isPatchingStatus}
            data-testid="toggle-enabled"
          />
          <Text>Automate privacy requests with this integration</Text>
        </Flex>
        <Paragraph type="secondary" className="m-0">
          When off, Fides won&apos;t run privacy requests against data from this
          integration.
        </Paragraph>
      </Flex>

      {supportsDatasets && (
        <Flex vertical gap="small">
          <Flex justify="space-between" align="center">
            <Typography.Title level={5} className="m-0">
              Linked datasets
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
            Choose which datasets Fides traverses when fulfilling a request.
            Each dataset can be linked to one integration.
          </Paragraph>

          <Modal
            open={linkModalOpen}
            onCancel={closeLinkModal}
            title={
              <Flex justify="space-between" align="center" gap="small">
                <span>Link datasets</span>
                {selectedDatasetKeys.length > 0 && (
                  <Tag
                    className="mr-6"
                    data-testid="link-dataset-selected-count"
                  >
                    {selectedDatasetKeys.length} selected
                  </Tag>
                )}
              </Flex>
            }
            footer={
              <Flex justify="flex-end" gap="small">
                <Button
                  onClick={closeLinkModal}
                  data-testid="cancel-link-dataset-button"
                >
                  Cancel
                </Button>
                <Button
                  type="primary"
                  disabled={selectedDatasetKeys.length === 0}
                  loading={isLinkingSelected}
                  onClick={handleLinkSelected}
                  data-testid="confirm-link-datasets-button"
                >
                  {selectedDatasetKeys.length <= 1
                    ? "Link dataset"
                    : `Link ${selectedDatasetKeys.length} datasets`}
                </Button>
              </Flex>
            }
            width={720}
            wrapProps={{ "data-testid": "link-dataset-modal" }}
          >
            <Flex vertical gap="medium">
              <Input.Search
                placeholder="Search datasets..."
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
              <Table
                rowKey="fides_key"
                size="small"
                loading={isUnlinkedFetching}
                dataSource={filteredUnlinkedDatasets}
                columns={linkDatasetColumns}
                rowSelection={{
                  type: "checkbox",
                  selectedRowKeys: selectedDatasetKeys,
                  // Selection is preserved across search filtering, so a user
                  // can search → select → search → select → confirm. The
                  // returned `keys` are just the currently-visible page's
                  // selection, so merge with anything previously selected
                  // that's no longer in view.
                  preserveSelectedRowKeys: true,
                  onChange: (keys) => setSelectedDatasetKeys(keys as string[]),
                }}
                pagination={{ pageSize: 10, hideOnSinglePage: true }}
                scroll={{ y: 320 }}
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
              />
            </Flex>
          </Modal>

          {isLoadingLinkedDatasets ? (
            <div className="flex h-32 items-center justify-center">
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
                        loading={unlinkingKey === datasetConfig.fides_key}
                        disabled={
                          unlinkingKey !== null &&
                          unlinkingKey !== datasetConfig.fides_key
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
                          vertical
                          align="flex-start"
                          gap={4}
                          className="w-full font-normal"
                        >
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
                          {showFidesKey && (
                            <Tag className="max-w-full truncate font-mono text-xs">
                              {datasetConfig.fides_key}
                            </Tag>
                          )}
                        </Flex>
                      }
                      description={datasetConfig.ctl_dataset?.description}
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
