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
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { Editor } from "~/features/common/yaml/helpers";
import { useUpdateDatasetMutation } from "~/features/dataset";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  useGetDatasetProtectedFieldsQuery,
  useGetDatasetReachabilityQuery,
  usePatchConnectionDatasetsMutation,
} from "~/features/datastore-connections";
import { ConnectionType, Dataset } from "~/types/api";

import {
  selectCurrentDataset,
  selectCurrentPolicyKey,
  setCurrentDataset,
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
  const dispatch = useAppDispatch();
  const [updateDataset] = useUpdateDatasetMutation();
  const [patchConnectionDatasets] = usePatchConnectionDatasetsMutation();

  const isSaas = connectionType === ConnectionType.SAAS;

  const [localDataset, setLocalDataset] = useState<Dataset | undefined>();
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
        skip:
          isSaas ||
          !connectionKey ||
          !currentDataset?.fides_key ||
          !currentPolicyKey,
      },
    );

  const { data: protectedFields } = useGetDatasetProtectedFieldsQuery(
    {
      connectionKey,
      datasetKey: currentDataset?.fides_key || "",
    },
    {
      skip: !isSaas || !connectionKey || !currentDataset?.fides_key,
    },
  );

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

  // SaaS: store as Dataset object; DB: store as YAML string
  useEffect(() => {
    if (currentDataset?.ctl_dataset) {
      const cleaned = removeNulls(currentDataset.ctl_dataset);
      if (isSaas) {
        setLocalDataset(cleaned as Dataset);
      } else {
        setEditorContent(yaml.dump(cleaned));
      }
    }
  }, [currentDataset, isSaas]);

  useEffect(() => {
    if (
      !isSaas &&
      currentPolicyKey &&
      currentDataset?.fides_key &&
      connectionKey
    ) {
      refetchReachability();
    }
  }, [
    isSaas,
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

    let saasWarnings: Array<{ message: string }> = [];

    if (isSaas) {
      const result = await patchConnectionDatasets({
        connectionKey,
        datasets: [datasetValues],
      });

      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
        return;
      }

      const failedMessage = result.data?.failed?.[0]?.message;
      if (failedMessage) {
        messageApi.error(failedMessage);
        return;
      }

      const succeededDataset = result.data?.succeeded?.[0];
      if (succeededDataset) {
        dispatch(
          setCurrentDataset({
            fides_key: currentDataset.fides_key,
            ctl_dataset: succeededDataset,
          }),
        );
        // Refresh local state with server response (may have restored fields)
        setLocalDataset(removeNulls(succeededDataset) as Dataset);
      } else {
        messageApi.warning("No changes were saved.");
        return;
      }

      saasWarnings = result.data?.warnings ?? [];
    } else {
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
    }

    if (saasWarnings.length > 0) {
      messageApi.success(
        `Dataset saved — ${saasWarnings.length} protected field(s) were restored`,
      );
      saasWarnings.forEach((warning) => {
        messageApi.warning(warning.message);
      });
    } else {
      messageApi.success("Successfully modified dataset");
    }

    await refetchDatasets();
    if (!isSaas) {
      await refetchReachability();
    }
  };

  const handleRefresh = async () => {
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
          {!isSaas && <ClipboardButton copyText={editorContent} />}
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
              protectedFields={protectedFields}
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
              message={
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
