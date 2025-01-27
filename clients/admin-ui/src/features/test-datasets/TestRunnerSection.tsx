import {
  AntButton as Button,
  AntSelect as Select,
  Heading,
  HStack,
  Text,
  Textarea,
  useToast,
  VStack,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";
import { useSelector } from "react-redux";

import { useAppDispatch } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";
import { getErrorMessage } from "~/features/common/helpers";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useGetDatasetInputsQuery,
  useTestDatastoreConnectionDatasetsMutation,
} from "~/features/datastore-connections";
import { useGetFilteredResultsQuery } from "~/features/privacy-requests";
import { PrivacyRequestStatus } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { useGetPoliciesQuery } from "../policy/policy.slice";
import {
  finishTest,
  selectCurrentDataset,
  selectCurrentPolicyKey,
  selectIsReachable,
  selectIsTestRunning,
  selectPrivacyRequestId,
  selectTestInputs,
  selectTestResults,
  setCurrentPolicyKey,
  setPrivacyRequestId,
  setTestInputs,
  setTestResults,
  startTest,
} from "./dataset-test.slice";

interface TestResultsSectionProps {
  connectionKey: string;
}

const TestResultsSection = ({ connectionKey }: TestResultsSectionProps) => {
  const toast = useToast();
  const dispatch = useAppDispatch();
  const [testDatasets] = useTestDatastoreConnectionDatasetsMutation();

  const currentDataset = useSelector(selectCurrentDataset);
  const isReachable = useSelector(selectIsReachable);
  const testResults = useSelector(selectTestResults);
  const testInputs = useSelector(selectTestInputs);
  const currentPolicyKey = useSelector(selectCurrentPolicyKey);
  const isTestRunning = useSelector(selectIsTestRunning);
  const privacyRequestId = useSelector(selectPrivacyRequestId);

  const [inputValue, setInputValue] = useState("{}");

  useEffect(() => {
    if (currentDataset) {
      setInputValue(JSON.stringify(testInputs, null, 2));
    }
  }, [currentDataset, testInputs]);

  // Poll for results when we have a privacy request ID
  const { data: filteredResults } = useGetFilteredResultsQuery(
    { privacy_request_id: privacyRequestId! },
    {
      skip: !privacyRequestId || !currentDataset?.fides_key,
      pollingInterval: 2000,
    },
  );

  // Get dataset inputs
  const { refetch: refetchInputs } = useGetDatasetInputsQuery(
    {
      connectionKey,
      datasetKey: currentDataset?.fides_key || "",
    },
    {
      skip: !connectionKey || !currentDataset?.fides_key,
      refetchOnMountOrArgChange: true,
    },
  );

  const { data: policies } = useGetPoliciesQuery();
  const policyOptions = useMemo(
    () =>
      (policies?.items || [])
        .filter((policy) =>
          policy.rules?.some((rule) => rule.action_type === "access"),
        )
        .map((item) => ({
          value: item.key,
          label: item.name,
        })),
    [policies?.items],
  );

  useEffect(() => {
    const datasetKey = currentDataset?.fides_key;

    if (connectionKey && datasetKey) {
      // First refetch to ensure we have latest data
      refetchInputs().then((response) => {
        // Only set inputs if we got valid data for the current dataset
        if (response.data && currentDataset?.fides_key === datasetKey) {
          dispatch(
            setTestInputs({
              datasetKey,
              values: response.data,
            }),
          );
        }
      });
    }
  }, [currentDataset, connectionKey, dispatch, refetchInputs]);

  // Handle filtered results updates
  useEffect(() => {
    const currentDatasetKey = currentDataset?.fides_key;

    if (
      !filteredResults ||
      filteredResults.privacy_request_id !== privacyRequestId ||
      !currentDatasetKey
    ) {
      return;
    }

    // Create the results action with the current dataset key
    const resultsAction = {
      datasetKey: currentDatasetKey,
      values: JSON.stringify(filteredResults, null, 2),
    };

    if (filteredResults.status === PrivacyRequestStatus.COMPLETE) {
      if (isTestRunning) {
        dispatch(setTestResults(resultsAction));
        dispatch(finishTest());
        toast(successToastParams("Test run completed successfully"));
      }
    } else if (filteredResults.status === PrivacyRequestStatus.ERROR) {
      dispatch(setTestResults(resultsAction));
      dispatch(finishTest());
      toast(errorToastParams("Test run failed"));
    }
  }, [
    filteredResults,
    privacyRequestId,
    currentDataset,
    isTestRunning,
    dispatch,
    toast,
  ]);

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = event.target.value;
    setInputValue(newValue);
    try {
      const parsedValue = JSON.parse(newValue);
      if (currentDataset) {
        dispatch(
          setTestInputs({
            datasetKey: currentDataset.fides_key,
            values: parsedValue,
          }),
        );
      }
    } catch (error) {
      // JSON will be invalid as the user types it out, this is expected
    }
  };

  const handlePolicyChange = (policyKey: string) => {
    dispatch(setCurrentPolicyKey(policyKey));
  };

  const currentPolicyKeyValue = useMemo(() => {
    if (!currentPolicyKey || !policies?.items) {
      return null;
    }
    return currentPolicyKey;
  }, [currentPolicyKey, policies?.items]);

  const handleTestRun = async () => {
    if (!currentDataset?.fides_key || !currentPolicyKey) {
      return;
    }

    try {
      let parsedInput;
      try {
        parsedInput = JSON.parse(inputValue);
      } catch (e) {
        toast(errorToastParams("Invalid JSON in test input"));
        return;
      }

      dispatch(startTest(currentDataset.fides_key));

      const result = await testDatasets({
        connection_key: connectionKey,
        dataset_key: currentDataset.fides_key,
        identities: parsedInput,
        policy_key: currentPolicyKey,
      });

      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        dispatch(finishTest());
      } else if ("data" in result) {
        dispatch(setPrivacyRequestId(result.data.privacy_request_id));
      } else {
        dispatch(finishTest());
        toast(errorToastParams("No privacy request ID in response"));
      }
    } catch (error) {
      dispatch(finishTest());
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
          <Text>Test inputs</Text>
          <ClipboardButton copyText={inputValue} />
        </HStack>
        <HStack>
          <Select
            id="policy"
            data-testid="policy-select"
            placeholder="Select policy"
            value={currentPolicyKeyValue}
            options={policyOptions}
            onChange={handlePolicyChange}
            className="w-64"
          />
          <Button
            htmlType="submit"
            size="small"
            type="primary"
            data-testid="run-btn"
            onClick={handleTestRun}
            loading={isTestRunning}
            disabled={!currentPolicyKey || !isReachable}
          >
            Run
          </Button>
          <QuestionTooltip label="Run a test access request using the provided test input data and the selected access policy" />
        </HStack>
      </Heading>
      <Textarea
        size="sm"
        focusBorderColor="primary.600"
        color="gray.800"
        isDisabled={isTestRunning}
        height="100%"
        value={inputValue}
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
