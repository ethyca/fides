import { useAlert } from "common/hooks/useAlert";
import {
  AntButton as Button,
  ConfirmationModal,
  Flex,
  HStack,
  Text,
  useDisclosure,
  VStack,
} from "fidesui";
import yaml, { YAMLException } from "js-yaml";
import React, { Fragment, useRef, useState } from "react";

import { Editor, isYamlException } from "~/features/common/yaml/helpers";
import YamlError from "~/features/common/yaml/YamlError";
import { useGetAllDatasetsQuery } from "~/features/dataset";
import { Dataset } from "~/types/api";

type YamlEditorFormProps = {
  data: Dataset[];
  isSubmitting: boolean;
  onSubmit: (value: unknown) => void;
  onCancel?: () => void;
  disabled?: boolean;
};

const YamlEditorForm = ({
  data = [],
  isSubmitting = false,
  onSubmit,
  onCancel,
  disabled,
}: YamlEditorFormProps) => {
  const monacoRef = useRef(null);
  const { errorAlert } = useAlert();
  const yamlData = data.length > 0 ? yaml.dump(data) : undefined;
  const [yamlError, setYamlError] = useState(
    undefined as unknown as YAMLException,
  );
  const [isTouched, setIsTouched] = useState(false);
  const [isEmptyState, setIsEmptyState] = useState(!yamlData);
  const warningDisclosure = useDisclosure();
  const { data: allDatasets } = useGetAllDatasetsQuery();
  const [overWrittenKeys, setOverWrittenKeys] = useState<string[]>([]);

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

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleMount = (editor: any, _monaco: any) => {
    monacoRef.current = editor;
    (monacoRef.current as any).focus();
  };

  const handleSubmit = () => {
    const value = (monacoRef.current as any).getValue();
    const yamlDoc = yaml.load(value, { json: true });
    onSubmit(yamlDoc);
    setOverWrittenKeys([]);
  };

  const handleConfirmation = () => {
    // Only need the confirmation if we are overwriting, which only happens when
    // there are already datasets
    if (allDatasets && allDatasets.length) {
      const value: string = (monacoRef.current as any).getValue();
      // Check if the fides key that is in the editor is the same as one that already exists
      // If so, then it is an overwrite and we should open the confirmation modal
      const overlappingKeys = allDatasets
        .filter((d) => value.includes(`fides_key: ${d.fides_key}\n`))
        .map((d) => d.fides_key);
      setOverWrittenKeys(overlappingKeys);
      if (overlappingKeys.length) {
        warningDisclosure.onOpen();
        return;
      }
    }
    handleSubmit();
  };

  return (
    <Flex gap="97px">
      <VStack align="stretch" w="800px">
        <Editor
          defaultLanguage="yaml"
          defaultValue={yamlData}
          height="calc(100vh - 526px)"
          onChange={handleChange}
          onMount={handleMount}
          options={{
            fontFamily: "Menlo",
            fontSize: 13,
            minimap: {
              enabled: true,
            },
            readOnly: disabled,
          }}
          theme="light"
        />
        <HStack justifyContent="flex-end" pr={6}>
          {onCancel && <Button onClick={onCancel}>Cancel</Button>}
          <Button
            type="primary"
            disabled={disabled || isEmptyState || !!yamlError || isSubmitting}
            loading={isSubmitting}
            onClick={handleConfirmation}
            htmlType="submit"
            data-testid="save-yaml-btn"
          >
            Save
          </Button>
        </HStack>
      </VStack>
      {isTouched && (isEmptyState || yamlError) && (
        <YamlError isEmptyState={isEmptyState} yamlError={yamlError} />
      )}
      <ConfirmationModal
        isOpen={warningDisclosure.isOpen}
        onClose={warningDisclosure.onClose}
        onConfirm={() => {
          handleSubmit();
          warningDisclosure.onClose();
        }}
        title="Overwrite dataset"
        message={
          <>
            <Text>
              You are about to overwrite the dataset
              {overWrittenKeys.length > 1 ? "s" : ""}{" "}
              {overWrittenKeys.map((key, i) => {
                const isLast = i === overWrittenKeys.length - 1;
                return (
                  <Fragment key={key}>
                    <Text color="complimentary.500" as="span" fontWeight="bold">
                      {key}
                    </Text>
                    {isLast ? "." : ", "}
                  </Fragment>
                );
              })}
            </Text>
            <Text>Are you sure you would like to continue?</Text>
          </>
        }
      />
    </Flex>
  );
};

export default YamlEditorForm;
