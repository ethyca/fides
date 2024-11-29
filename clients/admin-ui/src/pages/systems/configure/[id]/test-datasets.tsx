import {
  AntButton as Button,
  AntSelect as Select,
  Box,
  ErrorWarningIcon,
  GreenCheckCircleIcon,
  Heading,
  HStack,
  Stack,
  Text,
  Textarea,
  useToast,
  VStack,
} from "fidesui";
import yaml from "js-yaml";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useRef, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";
import FidesSpinner from "~/features/common/FidesSpinner";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { Editor } from "~/features/common/yaml/helpers";
import { useUpdateDatasetMutation } from "~/features/dataset";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  useGetDatasetInputsQuery,
  useGetDatasetReachabilityQuery,
  useTestDatastoreConnectionDatasetsMutation,
} from "~/features/datastore-connections";
import { useGetFilteredResultsQuery } from "~/features/privacy-requests";
import {
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "~/features/system";
import { Dataset, DatasetConfigSchema } from "~/types/api";
import { isErrorResult } from "~/types/errors";

// Types
interface DatasetOption {
  value: string;
  label: string;
}

// Helper functions
const getSystemId = (query: { id?: string | string[] }): string => {
  if (!query.id) {
    return "";
  }
  return Array.isArray(query.id) ? query.id[0] : query.id;
};

const createDatasetOptions = (
  items: DatasetConfigSchema[] = [],
): DatasetOption[] => {
  return items.map((item) => ({
    value: item.fides_key,
    label: item.fides_key,
  }));
};

interface EditorSectionProps {
  connectionKey: string;
  selectedDataset: DatasetConfigSchema | null;
  datasetOptions: DatasetOption[];
  onDatasetChange: (value: string) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

// Components
const EditorSection = ({
  connectionKey,
  selectedDataset,
  datasetOptions,
  onDatasetChange,
  onRefresh,
  isRefreshing,
}: EditorSectionProps) => {
  const [updateDataset, { isLoading }] = useUpdateDatasetMutation();
  const toast = useToast();
  const [editorContent, setEditorContent] = useState("");

  // Updated to use the connectionKey prop
  const {
    data: isReachable,
    refetch: refetchReachability,
    error: reachabilityError,
    isLoading: isReachabilityLoading,
  } = useGetDatasetReachabilityQuery(
    {
      connectionKey,
      datasetKey: selectedDataset?.fides_key || "",
    },
    {
      skip: !connectionKey || !selectedDataset?.fides_key,
    },
  );
  // Updated to use connectionKey prop
  useEffect(() => {
    if (connectionKey && selectedDataset?.fides_key) {
      refetchReachability();
    }
  }, [connectionKey, selectedDataset?.fides_key, refetchReachability]);

  // Update editor content when selected dataset changes
  useEffect(() => {
    if (selectedDataset?.ctl_dataset) {
      setEditorContent(yaml.dump(selectedDataset.ctl_dataset));
    }
  }, [selectedDataset]);

  const handleEditorChange = (value: string | undefined) => {
    setEditorContent(value || "");
  };

  const handleRefresh = async () => {
    try {
      await onRefresh();
      // Reset editor content to the original dataset
      if (selectedDataset?.ctl_dataset) {
        setEditorContent(yaml.dump(selectedDataset.ctl_dataset));
      }
      toast(successToastParams("Successfully refreshed datasets"));
    } catch (error) {
      toast(errorToastParams(error as string));
    }
  };

  const handleSave = async () => {
    try {
      const datasetValues = yaml.load(editorContent) as Partial<Dataset>;
      const updatedDataset = {
        ...selectedDataset!.ctl_dataset,
        ...datasetValues,
      };
      try {
        const result = await updateDataset(updatedDataset);
        if (isErrorResult(result)) {
          toast(errorToastParams(getErrorMessage(result.error)));
        } else {
          toast(successToastParams("Successfully modified dataset"));
          await refetchReachability();
        }
      } catch (error) {
        toast(errorToastParams(error as string));
      }
    } catch (yamlError) {
      toast(errorToastParams("Invalid YAML format"));
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
            value={selectedDataset?.fides_key || ""}
            options={datasetOptions}
            onChange={onDatasetChange}
            className="w-64"
          />
          <ClipboardButton copyText={editorContent} />
        </HStack>
        <HStack spacing={2}>
          <Button
            htmlType="submit"
            size="small"
            data-testid="save-btn"
            onClick={handleRefresh}
            loading={isRefreshing}
          >
            Refresh
          </Button>
          <Button
            htmlType="submit"
            size="small"
            onClick={handleSave}
            loading={isLoading}
          >
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
          value={editorContent}
          height="100%"
          onChange={handleEditorChange}
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
        justifyContent="space-between"
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
              <ErrorWarningIcon className="text-red-500" /> Dataset is not
              reachable
            </>
          )}
        </Text>
      </Stack>
    </VStack>
  );
};

const TestResultsSection = ({
  connectionKey,
  selectedDataset,
}: {
  connectionKey: string;
  selectedDataset: DatasetConfigSchema | null;
}) => {
  const toast = useToast();
  const [testDatasets] = useTestDatastoreConnectionDatasetsMutation();
  const [testInput, setTestInput] = useState({});
  const [testResults, setTestResults] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [privacyRequestId, setPrivacyRequestId] = useState<string | null>(null);

  // Poll for results when we have a privacy request ID
  const { data: filteredResults } = useGetFilteredResultsQuery(
    { privacy_request_id: privacyRequestId! },
    {
      skip: !privacyRequestId,
      pollingInterval: 2000, // Poll every 2 seconds
    },
  );

  useEffect(() => {
    if (!filteredResults) return;

    console.log("Filtered results:", filteredResults);

    if (
      filteredResults.status === "complete" ||
      filteredResults.status === "error"
    ) {
      if (filteredResults.status === "complete") {
        setTestResults(JSON.stringify(filteredResults.results, null, 2));
        toast(successToastParams("Test run completed successfully"));
      } else {
        toast(errorToastParams("Test run failed"));
      }
      setIsLoading(false);
      setPrivacyRequestId(null); // Stop polling by clearing the ID
    }
  }, [filteredResults, toast]);

  // Keep track of values for each dataset
  const datasetValuesRef = useRef<Record<string, Record<string, any>>>({});

  const { data: inputsData, error: inputsError } = useGetDatasetInputsQuery(
    {
      connectionKey,
      datasetKey: selectedDataset?.fides_key || "",
    },
    {
      skip: !connectionKey || !selectedDataset?.fides_key,
    },
  );

  useEffect(() => {
    if (!selectedDataset?.fides_key || !inputsData) return;

    try {
      const existingValues =
        datasetValuesRef.current[selectedDataset.fides_key] || {};

      const currentInputValues = testInput ? JSON.parse(testInput) : {};

      const filteredValues: Record<string, any> = {};
      Object.keys(inputsData).forEach((key) => {
        if (key in existingValues) {
          filteredValues[key] = existingValues[key];
        }
        if (key in currentInputValues) {
          filteredValues[key] = currentInputValues[key];
        }
        if (!(key in filteredValues)) {
          filteredValues[key] = inputsData[key];
        }
      });

      datasetValuesRef.current[selectedDataset.fides_key] = filteredValues;
      setTestInput(JSON.stringify(filteredValues, null, 2));
    } catch (e) {
      console.error("Error parsing test input:", e);
      setTestInput(JSON.stringify(inputsData, null, 2));
    }
  }, [inputsData, selectedDataset?.fides_key]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    setTestInput(newValue);

    if (selectedDataset?.fides_key && inputsData) {
      try {
        const parsedValues = JSON.parse(newValue);
        const validKeys = Object.keys(inputsData);

        const filteredValues: Record<string, any> = {};
        validKeys.forEach((key) => {
          if (key in parsedValues) {
            filteredValues[key] = parsedValues[key];
          }
        });

        datasetValuesRef.current[selectedDataset.fides_key] = filteredValues;
      } catch (e) {
        console.error("Error parsing modified input:", e);
      }
    }
  };

  const handleTestRun = async () => {
    try {
      setIsLoading(true);
      setTestResults(""); // Clear previous results

      let parsedInput;
      try {
        parsedInput = JSON.parse(testInput);
      } catch (e) {
        toast(errorToastParams("Invalid JSON in test input"));
        setIsLoading(false);
        return;
      }

      const result = await testDatasets({
        connection_key: connectionKey,
        dataset_key: selectedDataset?.fides_key || "",
        input_data: parsedInput,
      });

      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        setIsLoading(false);
      } else if ("data" in result) {
        // If the response is just a string, use it directly
        setPrivacyRequestId(result.data);
      } else {
        setIsLoading(false);
        toast(errorToastParams("No privacy request ID in response"));
      }
    } catch (error) {
      setIsLoading(false);
      toast(errorToastParams("Failed to start test run"));
    }
  };

  return (
    <VStack alignItems="stretch" flex="1" maxWidth="70vw" minHeight="0">
      <Heading
        as="h3"
        size="sm"
        display="flex"
        alignItems="center"
        justifyContent="space-between"
      >
        <HStack>
          <Text>Test inputs (identities and references)</Text>
          <ClipboardButton copyText={testInput} />
        </HStack>
        <Button
          htmlType="submit"
          size="small"
          type="primary"
          data-testid="save-btn"
          onClick={handleTestRun}
          loading={isLoading}
        >
          Run
        </Button>
      </Heading>
      <Textarea
        size="sm"
        focusBorderColor="primary.600"
        color="gray.800"
        isDisabled={isLoading}
        height="100%"
        value={testInput}
        onChange={handleInputChange}
      />
      <Heading as="h3" size="sm">
        Test results <ClipboardButton copyText={testResults} />
      </Heading>
      <Textarea
        isReadOnly
        size="sm"
        focusBorderColor="primary.600"
        color="gray.800"
        isDisabled={false}
        height="100%"
        value={testResults}
      />
    </VStack>
  );
};

const TestDatasetPage: NextPage = () => {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [selectedDataset, setSelectedDataset] =
    useState<DatasetConfigSchema | null>(null);

  const systemId = getSystemId(router.query);

  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId, {
    skip: !systemId,
  });

  const {
    data: datasetConfigs,
    isLoading: isDatasetConfigsLoading,
    refetch: refetchDatasets,
  } = useGetConnectionConfigDatasetConfigsQuery(
    system?.connection_configs?.key || "",
    {
      skip: !system?.connection_configs?.key,
    },
  );

  useEffect(() => {
    if (datasetConfigs?.items[0]) {
      setSelectedDataset(datasetConfigs.items[0]);
    }
  }, [datasetConfigs]);

  useEffect(() => {
    dispatch(setActiveSystem(system));
  }, [system, dispatch]);

  const handleDatasetChange = (value: string) => {
    const selectedConfig = datasetConfigs?.items.find(
      (item) => item.fides_key === value,
    );
    if (selectedConfig) {
      setSelectedDataset(selectedConfig);
    }
  };

  const handleRefresh = async () => {
    await refetchDatasets();
  };

  if (isLoading) {
    return (
      <Layout title="Systems">
        <FidesSpinner />
      </Layout>
    );
  }

  const datasetOptions = createDatasetOptions(datasetConfigs?.items);

  return (
    <Layout
      title="System inventory"
      mainProps={{
        paddingTop: 0,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <PageHeader
        breadcrumbs={[
          { title: "System inventory", link: SYSTEM_ROUTE },
          {
            title: system?.name || "",
            link: `/systems/configure/${systemId}#integrations`,
          },
          { title: "Test datasets" },
        ]}
        isSticky
      >
        <Box position="relative" />
      </PageHeader>
      <HStack
        alignItems="stretch"
        flex="1"
        minHeight="0"
        spacing="4"
        padding="4 4 4 0"
      >
        <EditorSection
          connectionKey={system?.connection_configs?.key || ""}
          selectedDataset={selectedDataset}
          datasetOptions={datasetOptions}
          onDatasetChange={handleDatasetChange}
          onRefresh={handleRefresh}
          isRefreshing={isDatasetConfigsLoading}
        />
        <TestResultsSection
          connectionKey={system?.connection_configs?.key || ""}
          selectedDataset={selectedDataset}
        />
      </HStack>
    </Layout>
  );
};

export default TestDatasetPage;
