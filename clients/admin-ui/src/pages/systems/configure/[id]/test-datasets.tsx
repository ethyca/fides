import {
  Box,
  GreenCheckCircleIcon,
  Heading,
  HStack,
  Stack,
  AntButton as Button,
  AntSelect as Select,
  Text,
  Textarea,
  VStack,
  useToast,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { useAppDispatch } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";
import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { Editor } from "~/features/common/yaml/helpers";
import { useGetConnectionConfigDatasetConfigsQuery } from "~/features/datastore-connections";
import {
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "~/features/system";
import yaml from "js-yaml";
import { Dataset, DatasetConfigSchema } from "~/types/api";
import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { isErrorResult } from "~/types/errors";
import { useUpdateDatasetMutation } from "~/features/dataset";

// Types
interface DatasetOption {
  value: string;
  label: string;
}

// Helper functions
const getSystemId = (query: { id?: string | string[] }): string => {
  if (!query.id) return "";
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

// Components
const EditorSection: React.FC<{
  selectedDataset: DatasetConfigSchema | null;
  datasetOptions: DatasetOption[];
  onDatasetChange: (value: string) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}> = ({
  selectedDataset,
  datasetOptions,
  onDatasetChange,
  onRefresh,
  isRefreshing,
}) => {
  const [updateDataset, { isLoading }] = useUpdateDatasetMutation();
  const toast = useToast();
  const [editorContent, setEditorContent] = useState("");

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
        backgroundColor="gray.50"
        border="1px solid"
        borderColor="green.500"
        borderRadius="md"
        justifyContent="space-between"
        py={2}
        px={4}
      >
        <Text fontSize="sm">
          <GreenCheckCircleIcon /> Dataset is reachable via the <b>email</b>{" "}
          identity
        </Text>
      </Stack>
    </VStack>
  );
};

const TestResultsSection: React.FC = () => {
  const [testInput, setTestInput] = useState(
    JSON.stringify({ email: "user@example.com" }, null, 2),
  );
  const [sqlQuery] = useState(
    "SELECT * FROM customer WHERE email='user@example.com'",
  );
  const [testResults] = useState(
    JSON.stringify({ customer: [{ first_name: "Test" }] }, null, 2),
  );

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
        >
          Run
        </Button>
      </Heading>
      <Textarea
        size="sm"
        focusBorderColor="primary.600"
        color="gray.800"
        isDisabled={false}
        height="100%"
        value={testInput}
        onChange={(e) => setTestInput(e.target.value)}
      />
      <Heading as="h3" size="sm">
        Generated SQL queries <ClipboardButton copyText={sqlQuery} />
      </Heading>
      <Textarea
        isReadOnly
        size="sm"
        focusBorderColor="primary.600"
        color="gray.800"
        isDisabled={false}
        height="100%"
        value={sqlQuery}
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
          selectedDataset={selectedDataset}
          datasetOptions={datasetOptions}
          onDatasetChange={handleDatasetChange}
          onRefresh={handleRefresh}
          isRefreshing={isDatasetConfigsLoading}
        />
        <TestResultsSection />
      </HStack>
    </Layout>
  );
};

export default TestDatasetPage;
