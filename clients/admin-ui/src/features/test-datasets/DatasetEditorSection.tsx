import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
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
import yaml, { YAMLException } from "js-yaml";
import { useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
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

const EditorSection = ({ connectionKey }: EditorSectionProps) => {
  const toast = useToast();
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
      toast(
        errorToastParams(
          `YAML Parsing Error: ${
            yamlError instanceof YAMLException
              ? `${yamlError.reason} ${yamlError.mark ? `at line ${yamlError.mark.line}` : ""}`
              : "Invalid YAML format"
          }`,
        ),
      );
      return;
    }

    // Then handle the API update
    const result = await updateDataset(datasetValues);

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }

    dispatch(
      setCurrentDataset({
        fides_key: currentDataset.fides_key,
        ctl_dataset: result.data,
      }),
    );
    toast(successToastParams("Successfully modified dataset"));
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
            value={currentDataset?.fides_key || ""}
            options={datasetOptions}
            onChange={handleDatasetChange}
            className="w-64"
          />
          <ClipboardButton copyText={editorContent} />
        </HStack>
        <HStack spacing={2}>
          <Button
            htmlType="submit"
            size="small"
            data-testid="refresh-btn"
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
        flex="1 1 auto"
        minHeight="200px"
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
      </Stack>
      {reachability && (
        <Stack
          backgroundColor={reachability?.reachable ? "green.50" : "red.50"}
          border="1px solid"
          borderColor={reachability?.reachable ? "green.500" : "red.500"}
          borderRadius="md"
          p={2}
          flexShrink={0}
          mt={2}
        >
          <HStack alignItems="center">
            <HStack flex="1">
              {reachability?.reachable ? (
                <GreenCheckCircleIcon />
              ) : (
                <ErrorWarningIcon />
              )}
              <Text fontSize="sm" whiteSpace="pre-wrap">
                {reachability?.reachable
                  ? "Dataset is reachable"
                  : `Dataset is not reachable. ${reachability?.details}`}
              </Text>
            </HStack>
          </HStack>
        </Stack>
      )}
    </VStack>
  );
};

export default EditorSection;
