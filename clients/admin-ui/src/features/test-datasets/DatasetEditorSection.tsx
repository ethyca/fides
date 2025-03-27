import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import {
  AntButton as Button,
  AntSelect as Select,
  Box,
  ErrorWarningIcon,
  GreenCheckCircleIcon,
  HStack,
  Stack,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  Tooltip,
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
import { selectActiveSystem } from "~/features/system/system.slice";
import { ConnectionType, Dataset, SystemResponse } from "~/types/api";

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
  const toast = useToast();
  const dispatch = useAppDispatch();
  const [updateDataset] = useUpdateDatasetMutation();
  const [tabIndex, setTabIndex] = useState(0);

  const [editorContent, setEditorContent] = useState<string>("");
  const [saasConfigContent, setSaasConfigContent] = useState<string>("");
  const currentDataset = useAppSelector(selectCurrentDataset);
  const currentPolicyKey = useAppSelector(selectCurrentPolicyKey);
  const activeSystem = useAppSelector(selectActiveSystem) as SystemResponse;
  const connectionConfig = activeSystem?.connection_configs || null;
  const isSaasConnector =
    connectionConfig?.connection_type === ConnectionType.SAAS;

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

  useEffect(() => {
    if (isSaasConnector && connectionConfig?.saas_config) {
      setSaasConfigContent(
        yaml.dump(removeNulls(connectionConfig.saas_config)),
      );
    }
  }, [connectionConfig, isSaasConnector]);

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

  // Get appropriate content for the clipboard button based on current tab
  const getClipboardContent = () => {
    if (tabIndex === 0) {
      return editorContent;
    }
    if (tabIndex === 1 && isSaasConnector) {
      return saasConfigContent;
    }
    return "";
  };

  return (
    <VStack
      alignItems="stretch"
      flex="1"
      maxWidth="70vw"
      maxHeight="50vh"
      spacing={2}
      mb={0}
    >
      <HStack justifyContent="space-between" alignItems="center">
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
        </HStack>
        <HStack spacing={2}>
          <Tooltip
            label="Refresh to load the latest data from the database. This will overwrite any unsaved local changes."
            hasArrow
            placement="top"
          >
            <Button
              htmlType="submit"
              size="small"
              data-testid="refresh-btn"
              onClick={handleRefresh}
              loading={isDatasetConfigsLoading}
            >
              Refresh
            </Button>
          </Tooltip>
          <Tooltip
            label="Save your changes to update the dataset in the database."
            hasArrow
            placement="top"
          >
            <Button htmlType="submit" size="small" onClick={handleSave}>
              Save
            </Button>
          </Tooltip>
        </HStack>
      </HStack>

      <Box position="relative" mb={0}>
        <Tabs
          index={tabIndex}
          onChange={setTabIndex}
          flex="1"
          variant="enclosed"
          size="sm"
          height="calc(45vh - 50px)"
        >
          <Box mb={0} borderBottom="none">
            <HStack alignItems="center" width="100%">
              <TabList mb="-1px" ml="4px">
                <Tab>Dataset</Tab>
                {isSaasConnector && <Tab>API configuration</Tab>}
              </TabList>
              <Box position="absolute" right="0" top="0" zIndex="1">
                <ClipboardButton copyText={getClipboardContent()} />
              </Box>
            </HStack>
          </Box>
          <TabPanels flex="1" height="calc(100% - 4px)">
            <TabPanel p={0} height="100%" pb={0}>
              <VStack
                flex="1"
                alignItems="stretch"
                spacing={2}
                height="100%"
                pb={0}
              >
                <Stack
                  border="1px solid"
                  borderColor="gray.200"
                  borderRadius="md"
                  justifyContent="space-between"
                  py={4}
                  pr={4}
                  data-testid="empty-state"
                  flex="1"
                  height="calc(100% - 40px)"
                  overflowY="auto"
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
                    backgroundColor={
                      reachability?.reachable ? "green.50" : "red.50"
                    }
                    border="1px solid"
                    borderColor={
                      reachability?.reachable ? "green.500" : "red.500"
                    }
                    borderRadius="md"
                    p={2}
                    flexShrink={0}
                    maxHeight="40px"
                    overflowY="hidden"
                    mb={0}
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
                            : `Dataset is not reachable. ${getReachabilityMessage(reachability?.details)}`}
                        </Text>
                      </HStack>
                    </HStack>
                  </Stack>
                )}
              </VStack>
            </TabPanel>
            {isSaasConnector && (
              <TabPanel p={0} height="100%" pb={0}>
                <VStack
                  flex="1"
                  alignItems="stretch"
                  spacing={2}
                  height="100%"
                  pb={0}
                >
                  <Stack
                    border="1px solid"
                    borderColor="gray.200"
                    borderRadius="md"
                    justifyContent="space-between"
                    py={4}
                    pr={4}
                    flex="1"
                    height="100%"
                    overflowY="auto"
                  >
                    <Editor
                      defaultLanguage="yaml"
                      value={saasConfigContent}
                      height="100%"
                      onMount={() => {}}
                      options={{
                        fontFamily: "Menlo",
                        fontSize: 13,
                        minimap: { enabled: false },
                        readOnly: true,
                        hideCursorInOverviewRuler: true,
                        overviewRulerBorder: false,
                        scrollBeyondLastLine: false,
                      }}
                      theme="light"
                    />
                  </Stack>
                </VStack>
              </TabPanel>
            )}
          </TabPanels>
        </Tabs>
      </Box>
    </VStack>
  );
};

export default EditorSection;
