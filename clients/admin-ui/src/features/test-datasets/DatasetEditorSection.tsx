import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import {
  AntButton as Button,
  AntSelect as Select,
  ErrorWarningIcon,
  GreenCheckCircleIcon,
  Heading,
  HStack,
  Stack,
  Text,
  useToast,
  VStack,
} from "fidesui";
import yaml from "js-yaml";
import { useEffect, useMemo, useState } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { Editor } from "~/features/common/yaml/helpers";
import { useUpdateDatasetMutation } from "~/features/dataset";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  useGetDatasetReachabilityQuery,
} from "~/features/datastore-connections";
import { Dataset, DatasetConfigSchema } from "~/types/api";

interface EditorSectionProps {
  connectionKey: string;
  onDatasetChange?: (dataset: DatasetConfigSchema | null) => void;
  onSaveOrRefresh?: () => void;
}

const EditorSection = ({
  connectionKey,
  onDatasetChange,
  onSaveOrRefresh,
}: EditorSectionProps) => {
  const toast = useToast();
  const [updateDataset] = useUpdateDatasetMutation();
  const [state, setState] = useState({
    selectedDataset: null as DatasetConfigSchema | null,
    editorContent: "",
  });

  const {
    data: datasetConfigs,
    isLoading: isDatasetConfigsLoading,
    refetch: refetchDatasets,
  } = useGetConnectionConfigDatasetConfigsQuery(connectionKey, {
    skip: !connectionKey,
  });

  const { data: isReachable, refetch: refetchReachability } =
    useGetDatasetReachabilityQuery(
      {
        connectionKey,
        datasetKey: state.selectedDataset?.fides_key || "",
      },
      {
        skip: !connectionKey || !state.selectedDataset?.fides_key,
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
    if (datasetConfigs?.items[0] && !state.selectedDataset) {
      const initialDataset = datasetConfigs.items[0];
      setState((prev) => ({ ...prev, selectedDataset: initialDataset }));
      onDatasetChange?.(initialDataset);
    }
  }, [datasetConfigs, state.selectedDataset, onDatasetChange]);

  const removeNulls = (obj: any): any => {
    if (Array.isArray(obj)) {
      return obj
        .map((item) => removeNulls(item))
        .filter((item) => item !== null);
    }
    if (obj && typeof obj === "object") {
      return Object.fromEntries(
        Object.entries(obj)
          .map(([key, value]) => [key, removeNulls(value)])
          .filter(([, value]) => value !== null),
      );
    }
    return obj;
  };

  useEffect(() => {
    if (state.selectedDataset?.ctl_dataset) {
      setState((prev) => ({
        ...prev,
        editorContent: yaml.dump(
          removeNulls(state.selectedDataset?.ctl_dataset),
        ),
      }));
    }
  }, [state.selectedDataset]);

  useEffect(() => {
    if (connectionKey && state.selectedDataset?.fides_key) {
      refetchReachability();
    }
  }, [connectionKey, state.selectedDataset?.fides_key, refetchReachability]);

  const handleDatasetChange = (value: string) => {
    const selectedConfig = datasetConfigs?.items.find(
      (item) => item.fides_key === value,
    );
    if (selectedConfig) {
      setState((prev) => ({ ...prev, selectedDataset: selectedConfig }));
      onDatasetChange?.(selectedConfig);
    }
  };

  const handleSave = async () => {
    try {
      const datasetValues = yaml.load(state.editorContent) as Partial<Dataset>;
      const updatedDataset = {
        ...state.selectedDataset!.ctl_dataset,
        ...datasetValues,
      };
      const result = await updateDataset(updatedDataset);
      if (isErrorResult(result)) {
        throw new Error(getErrorMessage(result.error));
      }
      await refetchReachability();
      onSaveOrRefresh?.();
      toast(successToastParams("Successfully modified dataset"));
    } catch (error) {
      toast(errorToastParams(getErrorMessage(error as FetchBaseQueryError)));
    }
  };

  const handleRefresh = async () => {
    try {
      const { data } = await refetchDatasets();
      const refreshedDataset = data?.items.find(
        (item) => item.fides_key === state.selectedDataset?.fides_key,
      );
      if (refreshedDataset?.ctl_dataset) {
        setState((prev) => ({
          ...prev,
          selectedDataset: refreshedDataset,
          editorContent: yaml.dump(removeNulls(refreshedDataset.ctl_dataset)),
        }));
      }
      onSaveOrRefresh?.();
      toast(successToastParams("Successfully refreshed datasets"));
    } catch (error) {
      toast(errorToastParams(getErrorMessage(error as FetchBaseQueryError)));
    }
  };

  return (
    <VStack alignItems="stretch" flex="1" maxWidth="70vw" maxHeight="100vh">
      <Heading
        as="h3"
        size="sm"
        display="flex"
        alignItems="center"
        justifyContent="space-between"
      >
        <HStack>
          <Text>Edit dataset: </Text>
          <Select
            id="format"
            data-testid="export-format-select"
            value={state.selectedDataset?.fides_key || ""}
            options={datasetOptions}
            onChange={handleDatasetChange}
            className="w-64"
          />
          <ClipboardButton copyText={state.editorContent} />
        </HStack>
        <HStack spacing={2}>
          <Button
            htmlType="submit"
            size="small"
            data-testid="save-btn"
            onClick={handleRefresh}
            loading={isDatasetConfigsLoading}
          >
            Refresh
          </Button>
          <Button htmlType="submit" size="small" onClick={handleSave}>
            Save
          </Button>
        </HStack>
      </Heading>
      <Stack
        border="1px solid"
        borderColor="gray.200"
        borderRadius="md"
        justifyContent="space-between"
        py={4}
        pr={4}
        data-testid="empty-state"
        height="100vh"
      >
        <Editor
          defaultLanguage="yaml"
          value={state.editorContent}
          height="100%"
          onChange={(value) =>
            setState((prev) => ({ ...prev, editorContent: value || "" }))
          }
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
      </Stack>
      <Stack
        backgroundColor={isReachable ? "green.50" : "red.50"}
        border="1px solid"
        borderColor={isReachable ? "green.500" : "red.500"}
        borderRadius="md"
        py={2}
        px={4}
      >
        <Text fontSize="sm">
          {isReachable ? (
            <>
              <GreenCheckCircleIcon /> Dataset is reachable
            </>
          ) : (
            <>
              <ErrorWarningIcon /> Dataset is not reachable
            </>
          )}
        </Text>
      </Stack>
    </VStack>
  );
};

export default EditorSection;
