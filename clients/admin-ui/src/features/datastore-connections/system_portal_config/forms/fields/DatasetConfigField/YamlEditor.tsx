import { useAlert } from "common/hooks/useAlert";
import { AntButton, Flex, ModalFooter, Text, VStack } from "fidesui";
import yaml, { YAMLException } from "js-yaml";
import React, { Fragment, useRef, useState } from "react";

import { Editor, isYamlException } from "~/features/common/yaml/helpers";
import YamlError from "~/features/common/yaml/YamlError";
import { useGetAllDatasetsQuery } from "~/features/dataset";
import { Dataset } from "~/types/api";

type YamlEditorFormProps = {
  data: Dataset[];
  isSubmitting: boolean;
  onChange: (value: Dataset) => void;
  onSubmit?: () => void;
  isLoading?: boolean;
  onCancel?: () => void;
  disabled?: boolean;
};

const YamlEditor = ({
  data = [],
  isSubmitting = false,
  onCancel,
  onSubmit,
  disabled,
  isLoading,
  onChange,
}: YamlEditorFormProps) => {
  const monacoRef = useRef(null);
  const { errorAlert } = useAlert();
  const yamlData = data.length > 0 ? yaml.dump(data) : undefined;
  const [yamlError, setYamlError] = useState(
    undefined as unknown as YAMLException,
  );
  const [isTouched, setIsTouched] = useState(false);
  const [isEmptyState, setIsEmptyState] = useState(!yamlData);
  /*
  We need to get all the datasets, including saas datasets, so that we can verify that
  the fides_key is not already in use.
   */
  const { data: allDatasets } = useGetAllDatasetsQuery();
  const [overWrittenKeys, setOverWrittenKeys] = useState<string[]>([]);

  const validate = (value: string) => {
    yaml.load(value, { json: true });
    setYamlError(undefined as unknown as YAMLException);
  };

  const checkForOverWrittenKeys = () => {
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
    }
  };

  const handleChange = (value: string | undefined) => {
    try {
      setIsTouched(true);
      validate(value as string);
      setIsEmptyState(!value || value.trim() === "");
      const yamlDoc = yaml.load(value || "", { json: true });
      if (Array.isArray(yamlDoc)) {
        onChange(yamlDoc[0] as Dataset);
      } else {
        onChange(yamlDoc as Dataset);
      }
      checkForOverWrittenKeys();
    } catch (error) {
      if (isYamlException(error)) {
        setYamlError(error);
      } else {
        errorAlert("Could not parse the supplied YAML");
      }
    }
  };

  const handleSubmit = () => {
    onSubmit?.();
    onCancel?.();
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleMount = (editor: any, _monaco: any) => {
    monacoRef.current = editor;
    (monacoRef.current as any).focus();
  };

  const submitDisabled =
    disabled || isEmptyState || !isTouched || !!yamlError || isSubmitting;

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
              enabled: false,
            },
            readOnly: disabled,
          }}
          theme="light"
        />
        {overWrittenKeys.length > 0 ? (
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
        ) : null}
        <ModalFooter>
          <div className="flex w-full justify-end gap-4">
            {onCancel && (
              <AntButton
                onClick={onCancel}
                data-testid="cancel-btn"
                disabled={isLoading}
              >
                Cancel
              </AntButton>
            )}
            <AntButton
              type="primary"
              onClick={handleSubmit}
              data-testid="continue-btn"
              disabled={submitDisabled}
              loading={isSubmitting || isLoading}
            >
              Confirm
            </AntButton>
          </div>
        </ModalFooter>
      </VStack>
      {isTouched && (isEmptyState || yamlError) && (
        <YamlError isEmptyState={isEmptyState} yamlError={yamlError} />
      )}
    </Flex>
  );
};

export default YamlEditor;
