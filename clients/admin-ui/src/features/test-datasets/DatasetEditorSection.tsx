import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  Alert,
  Button,
  Card,
  Flex,
  Icons,
  Select,
  Space,
  Tooltip,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import yaml, { YAMLException } from "js-yaml";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { Editor } from "~/features/common/yaml/helpers";
import { useUpdateDatasetMutation } from "~/features/dataset";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  useGetDatasetReachabilityQuery,
} from "~/features/datastore-connections";
import { ConnectionType, Dataset } from "~/types/api";

import {
  selectCurrentDataset,
  selectCurrentPolicyKey,
  setCurrentDataset,
  setReachability,
} from "./dataset-test.slice";
import DatasetNodeEditor from "./DatasetNodeEditor";
import { removeNulls } from "./helpers";

interface EditorSectionProps {
  connectionKey: string;
  connectionType?: ConnectionType;
}

const getReachabilityMessage = (details: any) => {
  if (Array.isArray(details)) {
    const firstDetail = details[0];

    if (!firstDetail) {
      return "";
    }

    const message = firstDetail.msg || "";
    const location = firstDetail.loc ? ` (${firstDetail.loc})` : "";
    return `${message}${location}`;
  }
  return details;
};

const EditorSection = ({
  connectionKey,
  connectionType,
}: EditorSectionProps) => {
  const messageApi = useMessage();
  const modal = useModal();
  const dispatch = useAppDispatch();
  const [updateDataset] = useUpdateDatasetMutation();

  const isSaas = connectionType === ConnectionType.SAAS;

  const [localDataset, setLocalDataset] = useState<Dataset | undefined>();
  const [editorContent, setEditorContent] = useState<string>("");
  const savedDatasetJson = useRef<string>("");
  const currentDataset = useAppSelector(selectCurrentDataset);
  const currentPolicyKey = useAppSelector(selectCurrentPolicyKey);

  const {
    data: datasetConfigs,
    isLoading: isDatasetConfigsLoading,
    refetch: refetchDatasets,
  } = useGetConnectionConfigDatasetConfigsQuery(connectionKey, {
    skip: !connectionKey,
    // Always refetch when the editor is opened: deleting + rebuilding an
    // integration with the same key otherwise serves cached ctl_dataset
    // (incl. stale user edits). Drilling into collections is in-memory and
    // doesn't re-fire this query.
    refetchOnMountOrArgChange: true,
  });

  // Reachability only applies on the test-datasets page (no connectionType),
  // where the user selects a policy. The edit-dataset page has no policy
  // selector, so showing reachability there would use stale global state.
  const { data: reachability, refetch: refetchReachability } =
    useGetDatasetReachabilityQuery(
      {
        connectionKey,
        datasetKey: currentDataset?.fides_key || "",
        policyKey: currentPolicyKey,
      },
      {
        skip:
          !!connectionType ||
          !connectionKey ||
          !currentDataset?.fides_key ||
          !currentPolicyKey,
      },
    );

  useEffect(() => {
    if (reachability) {
      dispatch(setReachability(reachability.reachable));
    }
  }, [reachability, dispatch]);
  const datasetOptions = useMemo(
    () =>
      (datasetConfigs?.items || []).map((item) => ({
        value: item.fides_key,
        label: item.fides_key,
      })),
    [datasetConfigs?.items],
  );

  useEffect(() => {
    if (!datasetConfigs?.items.length) {
      return;
    }
    // Always pull the freshest DatasetConfig from the server response into
    // Redux — not only on key mismatch. Otherwise deleting + rebuilding an
    // integration with the same fides_key keeps the previously-edited
    // ctl_dataset in Redux and re-seeds localDataset with stale fields.
    const matched = datasetConfigs.items.find(
      (item) => item.fides_key === currentDataset?.fides_key,
    );
    dispatch(setCurrentDataset(matched ?? datasetConfigs.items[0]));
    // currentDataset intentionally excluded from deps: we only want to re-sync
    // when a new server response arrives, not when Redux updates in response.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetConfigs, dispatch]);

  // SaaS: store as Dataset object; DB: store as YAML string
  useEffect(() => {
    if (currentDataset?.ctl_dataset) {
      const cleaned = removeNulls(currentDataset.ctl_dataset);
      if (isSaas) {
        setLocalDataset(cleaned as Dataset);
        savedDatasetJson.current = JSON.stringify(cleaned);
      } else {
        setEditorContent(yaml.dump(cleaned));
      }
    }
  }, [currentDataset, isSaas]);

  // Key-ordering stability: both savedDatasetJson and localDataset are produced
  // through the same removeNulls → JSON.stringify path, so key order is consistent.
  // If this assumption ever breaks (e.g., server returns keys in different order),
  // replace with a structural deep-equal.
  const isDirty = useMemo(() => {
    if (!isSaas || !localDataset) {
      return false;
    }
    return JSON.stringify(localDataset) !== savedDatasetJson.current;
  }, [isSaas, localDataset]);

  useEffect(() => {
    if (
      !connectionType &&
      currentPolicyKey &&
      currentDataset?.fides_key &&
      connectionKey
    ) {
      refetchReachability();
    }
  }, [
    connectionType,
    currentPolicyKey,
    currentDataset?.fides_key,
    connectionKey,
    refetchReachability,
  ]);

  const handleDatasetChange = async (value: string) => {
    const selectedConfig = datasetConfigs?.items.find(
      (item) => item.fides_key === value,
    );
    if (selectedConfig) {
      dispatch(setCurrentDataset(selectedConfig));
    }
  };

  const handleLocalDatasetChange = useCallback((updated: Dataset) => {
    setLocalDataset(updated);
  }, []);

  const handleSave = async () => {
    if (!currentDataset) {
      return;
    }

    let datasetValues: Dataset;
    if (isSaas) {
      if (!localDataset) {
        return;
      }
      datasetValues = localDataset;
    } else {
      try {
        datasetValues = yaml.load(editorContent) as Dataset;
      } catch (yamlError) {
        messageApi.error(
          `YAML Parsing Error: ${
            yamlError instanceof YAMLException
              ? `${yamlError.reason} ${yamlError.mark ? `at line ${yamlError.mark.line}` : ""}`
              : "Invalid YAML format"
          }`,
        );
        return;
      }
    }

    const result = await updateDataset(datasetValues);

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }

    dispatch(
      setCurrentDataset({
        fides_key: currentDataset.fides_key,
        ctl_dataset: result.data,
      }),
    );
    if (isSaas) {
      savedDatasetJson.current = JSON.stringify(removeNulls(result.data));
    }
    messageApi.success("Successfully modified dataset");
    await refetchDatasets();
    if (!connectionType && currentPolicyKey) {
      await refetchReachability();
    }
  };

  const doRefresh = async () => {
    try {
      const { data } = await refetchDatasets();
      const refreshedDataset = data?.items.find(
        (item) => item.fides_key === currentDataset?.fides_key,
      );
      if (refreshedDataset?.ctl_dataset) {
        const cleaned = removeNulls(refreshedDataset.ctl_dataset);
        if (isSaas) {
          setLocalDataset(cleaned as Dataset);
        } else {
          setEditorContent(yaml.dump(cleaned));
        }
      }
      messageApi.success("Successfully refreshed datasets");
    } catch (error) {
      messageApi.error(getErrorMessage(error as FetchBaseQueryError));
    }
  };

  const handleRefresh = () => {
    if (isDirty) {
      modal.confirm({
        title: "Unsaved changes",
        content:
          "You have unsaved changes that will be lost. Are you sure you want to refresh?",
        okText: "Discard and refresh",
        okButtonProps: { danger: true },
        cancelText: "Cancel",
        onOk: doRefresh,
      });
    } else {
      doRefresh();
    }
  };

  return (
    <Flex
      align="stretch"
      flex="1"
      gap="small"
      vertical
      style={{ height: "100%", minHeight: 0 }}
    >
      <Flex align="center" justify="space-between">
        <Space>
          <Typography.Title level={3} style={{ margin: 0 }}>
            Edit dataset:
          </Typography.Title>
          <Select
            id="format"
            aria-label="Select a dataset"
            data-testid="export-format-select"
            value={currentDataset?.fides_key || ""}
            options={datasetOptions}
            onChange={handleDatasetChange}
            className="w-64"
          />
        </Space>
        <Space>
          {isDirty && (
            <Typography.Text type="warning" style={{ fontSize: 12 }}>
              Unsaved changes
            </Typography.Text>
          )}
          {!isSaas && <ClipboardButton copyText={editorContent} />}
          <Tooltip
            title="Refresh to load the latest data from the database. This will overwrite any unsaved local changes."
            placement="top"
          >
            <Button
              data-testid="refresh-btn"
              onClick={handleRefresh}
              loading={isDatasetConfigsLoading}
              icon={<Icons.Renew />}
              aria-label="Refresh"
            />
          </Tooltip>

          <Button
            htmlType="submit"
            type="primary"
            disabled={!isDirty}
            onClick={handleSave}
          >
            Save
          </Button>
        </Space>
      </Flex>
      {isSaas ? (
        <div
          style={{
            flex: "1 1 auto",
            minHeight: 0,
            borderRadius: 8,
            overflow: "hidden",
            border: "1px solid var(--fidesui-neutral-200)",
          }}
        >
          {localDataset && (
            <DatasetNodeEditor
              dataset={localDataset}
              onDatasetChange={handleLocalDatasetChange}
            />
          )}
        </div>
      ) : (
        <>
          <Card
            data-testid="empty-state"
            className="flex flex-1"
            styles={{
              body: {
                minHeight: "200px",
                display: "flex",
                flex: "1 1 auto",
                paddingLeft: 0,
              },
            }}
          >
            <Editor
              defaultLanguage="yaml"
              value={editorContent}
              height="100%"
              onChange={(value) => setEditorContent(value || "")}
              options={{
                fontFamily: "Menlo",
                fontSize: 13,
                minimap: { enabled: false },
                readOnly: false,
                hideCursorInOverviewRuler: true,
                overviewRulerBorder: false,
                scrollBeyondLastLine: false,
              }}
              theme="light"
            />
          </Card>
          {reachability && (
            <Alert
              type={reachability?.reachable ? "success" : "error"}
              title={
                reachability?.reachable
                  ? "Dataset is reachable"
                  : `Dataset is not reachable. ${getReachabilityMessage(reachability?.details)}`
              }
              showIcon
            />
          )}
        </>
      )}
    </Flex>
  );
};

export default EditorSection;
