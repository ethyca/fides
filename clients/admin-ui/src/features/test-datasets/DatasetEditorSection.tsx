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
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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
  setReachability,
} from "./dataset-test.slice";
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

  const [editorContent, setEditorContent] = useState<string>("");
  const [editorReady, setEditorReady] = useState(false);
  const editorRef = useRef<any>(null);
  const decorationsRef = useRef<any>(null);
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

  const { data: protectedFields } = useGetDatasetProtectedFieldsQuery(
    {
      connectionKey,
      datasetKey: currentDataset?.fides_key || "",
    },
    {
      skip: !isSaas || !connectionKey || !currentDataset?.fides_key,
    },
  );

  /**
   * Compute decoration ranges from editorContent (React state, always in sync)
   * rather than from Monaco's model (which updates asynchronously).
   * Covers immutable top-level metadata + SaaS config referenced fields.
   */
  const protectedRanges = useMemo(() => {
    if (!isSaas || !protectedFields || !editorContent) {
      return [];
    }

    const lines = editorContent.split("\n");
    const ranges: any[] = [];

    const protectedPathsByCollection = new Map<string, Set<string>>();
    protectedFields.protected_collection_fields.forEach((pf) => {
      if (!protectedPathsByCollection.has(pf.collection)) {
        protectedPathsByCollection.set(pf.collection, new Set());
      }
      const pathSet = protectedPathsByCollection.get(pf.collection)!;
      const segments = pf.field.split(".");
      segments.forEach((_, idx) => {
        pathSet.add(segments.slice(0, idx + 1).join("."));
      });
    });

    const immutableSet = new Set(protectedFields.immutable_fields);
    let currentCollection = "";
    const fieldStack: [number, string][] = [];

    lines.forEach((line: string, i: number) => {
      let isProtected = false;

      if (/^\S/.test(line) && line.includes(":")) {
        const key = line.split(":")[0].trim();
        if (immutableSet.has(key)) {
          isProtected = true;
        }
      }

      const nameMatch = line.match(/^(\s*)-\s+name:\s+(\S+)/);
      if (nameMatch) {
        const [, indent, name] = nameMatch;
        const indentLevel = indent.length;

        if (indentLevel <= 4) {
          currentCollection = name;
          fieldStack.length = 0;
        } else {
          while (
            fieldStack.length > 0 &&
            fieldStack[fieldStack.length - 1][0] >= indentLevel
          ) {
            fieldStack.pop();
          }
          fieldStack.push([indentLevel, name]);

          if (protectedPathsByCollection.has(currentCollection)) {
            const currentPath = fieldStack.map(([, n]) => n).join(".");
            if (
              protectedPathsByCollection
                .get(currentCollection)!
                .has(currentPath)
            ) {
              isProtected = true;
            }
          }
        }
      }

      if (isProtected) {
        ranges.push({
          range: {
            startLineNumber: i + 1,
            startColumn: 1,
            endLineNumber: i + 1,
            endColumn: line.length + 1,
          },
          options: {
            isWholeLine: true,
            inlineClassName: "immutable-line",
          },
        });
      }
    });

    return ranges;
  }, [isSaas, protectedFields, editorContent]);

  // Apply precomputed ranges whenever they change or editor becomes available
  const applyProtectedDecorations = useCallback(() => {
    const editor = editorRef.current;
    if (!editor) {
      return;
    }
    decorationsRef.current = editor.deltaDecorations(
      decorationsRef.current || [],
      protectedRanges,
    );
  }, [protectedRanges]);

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
      setEditorContent(yaml.dump(removeNulls(currentDataset.ctl_dataset)));
    }
  }, [currentDataset]);

  // Apply decorations whenever ranges change or editor becomes ready
  useEffect(() => {
    if (editorReady) {
      applyProtectedDecorations();
    }
  }, [editorReady, applyProtectedDecorations]);

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

  const handleDatasetChange = async (value: string) => {
    const selectedConfig = datasetConfigs?.items.find(
      (item) => item.fides_key === value,
    );
    if (selectedConfig) {
      dispatch(setCurrentDataset(selectedConfig));
    }
  };

  const refreshEditorFromServer = async () => {
    try {
      const { data } = await refetchDatasets();
      const refreshedDataset = data?.items.find(
        (item) => item.fides_key === currentDataset?.fides_key,
      );
      if (refreshedDataset?.ctl_dataset) {
        setEditorContent(yaml.dump(removeNulls(refreshedDataset.ctl_dataset)));
      }
    } catch {
      // Silent — the primary error message is already shown
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

    // Use connection-aware endpoint for SaaS to enforce structural validation
    if (isSaas) {
      const result = await patchConnectionDatasets({
        connectionKey,
        datasets: [datasetValues],
      });

      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
        await refreshEditorFromServer();
        return;
      }

      // The endpoint returns 200 with BulkPutDataset — check for failures in the response
      const failedMessage = result.data?.failed?.[0]?.message;
      if (failedMessage) {
        messageApi.error(failedMessage);
        await refreshEditorFromServer();
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
      }
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
          onMount={(editor: any) => {
            editorRef.current = editor;
            decorationsRef.current = [];
            if (!document.getElementById("immutable-line-style")) {
              const style = document.createElement("style");
              style.id = "immutable-line-style";
              style.textContent = `.immutable-line { opacity: 0.5; }`;
              document.head.appendChild(style);
            }
            setEditorReady(true);
          }}
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
      {isSaas && protectedFields && (
        <Typography.Text type="secondary" className="text-xs">
          Greyed-out lines are protected and cannot be modified or deleted.
        </Typography.Text>
      )}
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
