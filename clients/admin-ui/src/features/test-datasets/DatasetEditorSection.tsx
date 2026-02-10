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
} from "fidesui";
import yaml, { YAMLException } from "js-yaml";
import { useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { Editor } from "~/features/common/yaml/helpers";
import { useUpdateDatasetMutation } from "~/features/dataset";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  useGetDatasetReachabilityQuery,
} from "~/features/datastore-connections";
import { Dataset } from "~/types/api";

import {
  selectCurrentDataset,
  selectCurrentPolicyKey,
  setCurrentDataset,
  setReachability,
} from "./dataset-test.slice";
import { removeNulls } from "./helpers";

interface EditorSectionProps {
  connectionKey: string;
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

const EditorSection = ({ connectionKey }: EditorSectionProps) => {
  const messageApi = useMessage();
  const dispatch = useAppDispatch();
  const [updateDataset] = useUpdateDatasetMutation();

  const [editorContent, setEditorContent] = useState<string>("");
  const currentDataset = useAppSelector(selectCurrentDataset);
  const currentPolicyKey = useAppSelector(selectCurrentPolicyKey);

  const {
    data: datasetConfigs,
    isLoading: isDatasetConfigsLoading,
    refetch: refetchDatasets,
  } = useGetConnectionConfigDatasetConfigsQuery(connectionKey, {
    skip: !connectionKey,
  });

  const { data: reachability, refetch: refetchReachability } =
    useGetDatasetReachabilityQuery(
      {
        connectionKey,
        datasetKey: currentDataset?.fides_key || "",
        policyKey: currentPolicyKey,
      },
      {
        skip: !connectionKey || !currentDataset?.fides_key || !currentPolicyKey,
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
    if (datasetConfigs?.items.length) {
      if (
        !currentDataset ||
        !datasetConfigs.items.find(
          (item) => item.fides_key === currentDataset.fides_key,
        )
      ) {
        const initialDataset = datasetConfigs.items[0];
        dispatch(setCurrentDataset(initialDataset));
      }
    }
  }, [datasetConfigs, currentDataset, dispatch]);

  useEffect(() => {
    if (currentDataset?.ctl_dataset) {
      setEditorContent(yaml.dump(removeNulls(currentDataset?.ctl_dataset)));
    }
  }, [currentDataset]);

  useEffect(() => {
    if (currentPolicyKey && currentDataset?.fides_key && connectionKey) {
      refetchReachability();
    }
  }, [
    currentPolicyKey,
    currentDataset?.fides_key,
    connectionKey,
    refetchReachability,
  ]);

  useEffect(() => {
    if (reachability) {
      dispatch(setReachability(reachability.reachable));
    }
  }, [reachability, dispatch]);

  const handleDatasetChange = async (value: string) => {
    const selectedConfig = datasetConfigs?.items.find(
      (item) => item.fides_key === value,
    );
    if (selectedConfig) {
      dispatch(setCurrentDataset(selectedConfig));
    }
  };

  const handleSave = async () => {
    if (!currentDataset) {
      return;
    }

    // Parse YAML first
    let datasetValues: Dataset;
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

    // Then handle the API update
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
    messageApi.success("Successfully modified dataset");
    await refetchDatasets();
    await refetchReachability();
  };

  const handleRefresh = async () => {
    try {
      const { data } = await refetchDatasets();
      const refreshedDataset = data?.items.find(
        (item) => item.fides_key === currentDataset?.fides_key,
      );
      if (refreshedDataset?.ctl_dataset) {
        setEditorContent(yaml.dump(removeNulls(refreshedDataset.ctl_dataset)));
      }
      messageApi.success("Successfully refreshed datasets");
    } catch (error) {
      messageApi.error(getErrorMessage(error as FetchBaseQueryError));
    }
  };

  return (
    <Flex
      align="stretch"
      flex="1"
      gap="small"
      className="max-h-screen max-w-[70vw]"
      vertical
    >
      <Flex align="center" justify="space-between">
        <Space>
          <Typography.Title level={3}>Edit dataset: </Typography.Title>
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
          <ClipboardButton copyText={editorContent} />
          <Tooltip
            title="Refresh to load the latest data from the database. This will overwrite any unsaved local changes."
            placement="top"
          >
            <Button
              size="small"
              data-testid="refresh-btn"
              onClick={handleRefresh}
              loading={isDatasetConfigsLoading}
              icon={<Icons.Renew />}
              aria-label="Refresh"
            />
          </Tooltip>
          <Tooltip
            title="Save your changes to update the dataset in the database."
            placement="top"
          >
            <Button htmlType="submit" size="small" onClick={handleSave}>
              Save
            </Button>
          </Tooltip>
        </Space>
      </Flex>
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
          onMount={() => {}}
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
          message={
            reachability?.reachable
              ? "Dataset is reachable"
              : `Dataset is not reachable. ${getReachabilityMessage(reachability?.details)}`
          }
          showIcon
        />
      )}
    </Flex>
  );
};

export default EditorSection;
