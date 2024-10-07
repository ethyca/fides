import {
  AntButton as Button,
  Box,
  Divider,
  Flex,
  useToast,
  VStack,
} from "fidesui";
import yaml, { YAMLException } from "js-yaml";
import { useRouter } from "next/router";
import { useRef, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { DATASET_DETAIL_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { Editor, isYamlException } from "~/features/common/yaml/helpers";
import YamlError from "~/features/common/yaml/YamlError";
import { Dataset } from "~/types/api";

import {
  setActiveDatasetFidesKey,
  useCreateDatasetMutation,
} from "./dataset.slice";

// handle the common case where everything is nested under a `dataset` key
interface NestedDataset {
  dataset: Dataset[];
}
export function isDatasetArray(value: unknown): value is NestedDataset {
  return (
    typeof value === "object" &&
    value != null &&
    "dataset" in value &&
    Array.isArray((value as any).dataset)
  );
}

const DatasetYamlForm = () => {
  const [createDataset] = useCreateDatasetMutation();
  const [isEmptyState, setIsEmptyState] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTouched, setIsTouched] = useState(false);
  const monacoRef = useRef(null);
  const router = useRouter();
  const toast = useToast();
  const { errorAlert } = useAlert();
  const [yamlError, setYamlError] = useState(
    undefined as unknown as YAMLException,
  );

  const validate = (value: string) => {
    yaml.load(value, { json: true });
    setYamlError(undefined as unknown as YAMLException);
  };

  const handleChange = (value: string | undefined) => {
    try {
      setIsTouched(true);
      validate(value as string);
      setIsEmptyState(!!(!value || value.trim() === ""));
    } catch (error) {
      if (isYamlException(error)) {
        setYamlError(error);
      } else {
        errorAlert("Could not parse the supplied YAML");
      }
    }
  };

  const handleCreate = async (value: unknown) => {
    let dataset;
    if (isDatasetArray(value)) {
      [dataset] = value.dataset;
    } else {
      dataset = value;
    }
    return createDataset(dataset);
  };

  const handleMount = (editor: any) => {
    monacoRef.current = editor;
    (monacoRef.current as any).focus();
  };

  const handleSuccess = (newDataset: Dataset) => {
    toast(successToastParams("Successfully loaded new dataset YAML"));
    setActiveDatasetFidesKey(newDataset.fides_key);
    router.push({
      pathname: DATASET_DETAIL_ROUTE,
      query: { datasetId: newDataset.fides_key },
    });
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    const value = (monacoRef.current as any).getValue();
    const yamlDoc = yaml.load(value, { json: true });
    const result = await handleCreate(yamlDoc);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else if ("data" in result) {
      handleSuccess(result.data);
    }
    setIsSubmitting(false);
  };

  return (
    <Flex gap="97px">
      <Box w="75%">
        <Box color="gray.700" fontSize="14px" mb={4}>
          Get started creating your first dataset by pasting your dataset yaml
          below! You may have received this yaml from a colleague or your Ethyca
          developer support engineer.
        </Box>
        <VStack align="stretch">
          <Divider color="gray.100" />
          <Editor
            defaultLanguage="yaml"
            height="calc(100vh - 515px)"
            onChange={handleChange}
            onMount={handleMount}
            options={{
              fontFamily: "Menlo",
              fontSize: 13,
              minimap: {
                enabled: true,
              },
            }}
            theme="light"
          />
          <Divider color="gray.100" />
          <Button
            type="primary"
            disabled={isEmptyState || !!yamlError || isSubmitting}
            loading={isSubmitting}
            onClick={handleSubmit}
            htmlType="submit"
            className="mt-6 w-fit"
          >
            Create dataset
          </Button>
        </VStack>
      </Box>
      <Box>
        {isTouched && (isEmptyState || yamlError) && (
          <YamlError isEmptyState={isEmptyState} yamlError={yamlError} />
        )}
      </Box>
    </Flex>
  );
};

export default DatasetYamlForm;
