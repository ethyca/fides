import {
  AntButton as Button,
  Heading,
  HStack,
  Text,
  Textarea,
  useToast,
  VStack,
} from "fidesui";
import { useEffect, useRef, useState } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useTestDatastoreConnectionDatasetsMutation } from "~/features/datastore-connections";
import { useGetFilteredResultsQuery } from "~/features/privacy-requests";
import { DatasetConfigSchema } from "~/types/api";
import { isErrorResult } from "~/types/errors";

interface TestResultsSectionProps {
  connectionKey: string;
  selectedDataset: DatasetConfigSchema | null;
  testInput: string;
  onInputChange: (value: string) => void;
}

const TestResultsSection = ({
  connectionKey,
  selectedDataset,
  testInput,
  onInputChange,
}: TestResultsSectionProps) => {
  const toast = useToast();
  const [testDatasets] = useTestDatastoreConnectionDatasetsMutation();
  const [testResults, setTestResults] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [privacyRequestId, setPrivacyRequestId] = useState<string | null>(null);

  // Keep track of results for each dataset
  const resultValuesRef = useRef<Record<string, Record<string, any>>>({});

  // Poll for results when we have a privacy request ID
  const { data: filteredResults } = useGetFilteredResultsQuery(
    { privacy_request_id: privacyRequestId! },
    {
      skip: !privacyRequestId,
      pollingInterval: 2000,
    },
  );

  // Handle dataset changes or results updates
  useEffect(() => {
    if (!selectedDataset?.fides_key) {
      setTestResults("");
      return;
    }

    const currentResults = resultValuesRef.current[selectedDataset.fides_key];
    setTestResults(
      currentResults ? JSON.stringify(currentResults, null, 2) : "",
    );
  }, [selectedDataset]);

  // Handle filtered results updates
  useEffect(() => {
    if (!filteredResults || !selectedDataset?.fides_key) {
      return;
    }

    if (
      filteredResults.status === "complete" ||
      filteredResults.status === "error"
    ) {
      if (filteredResults.status === "complete") {
        resultValuesRef.current[selectedDataset.fides_key] =
          filteredResults.results;
        setTestResults(JSON.stringify(filteredResults.results, null, 2));
        toast(successToastParams("Test run completed successfully"));
      } else {
        toast(errorToastParams("Test run failed"));
        delete resultValuesRef.current[selectedDataset.fides_key];
        setTestResults("");
      }
      setIsLoading(false);
      setPrivacyRequestId(null);
    }
  }, [filteredResults, toast]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onInputChange(e.target.value);
  };

  const handleTestRun = async () => {
    if (!selectedDataset?.fides_key) {
      return;
    }

    try {
      setIsLoading(true);
      setTestResults("");

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
        dataset_key: selectedDataset.fides_key,
        input_data: parsedInput,
      });

      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        setIsLoading(false);
      } else if ("data" in result) {
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

export default TestResultsSection;
