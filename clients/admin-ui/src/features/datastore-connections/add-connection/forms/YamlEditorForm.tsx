import { ConfirmationModal } from "@fidesui/components";
import {
  Box,
  Button,
  ButtonGroup,
  Divider,
  ErrorWarningIcon,
  Flex,
  Heading,
  HStack,
  SlideFade,
  Tag,
  Text,
  useDisclosure,
  VStack,
} from "@fidesui/react";
import { useAlert } from "common/hooks/useAlert";
import yaml, { YAMLException } from "js-yaml";
import { narrow } from "narrow-minded";
import dynamic from "next/dynamic";
import React, { useRef, useState } from "react";

import { useFeatures } from "~/features/common/features";
import { useGetAllDatasetsQuery } from "~/features/dataset";
import { Dataset } from "~/types/api";

const Editor = dynamic(
  // @ts-ignore
  () => import("@monaco-editor/react").then((mod) => mod.default),
  { ssr: false }
);

const isYamlException = (error: unknown): error is YAMLException =>
  narrow({ name: "string" }, error) && error.name === "YAMLException";

type YamlEditorFormProps = {
  data: Dataset[];
  isSubmitting: boolean;
  onSubmit: (value: unknown) => void;
  onCancel?: () => void;
  disabled?: boolean;
};

const YamlEditorForm: React.FC<YamlEditorFormProps> = ({
  data = [],
  isSubmitting = false,
  onSubmit,
  onCancel,
  disabled,
}) => {
  const monacoRef = useRef(null);
  const { errorAlert } = useAlert();
  const yamlData = data.length > 0 ? yaml.dump(data) : undefined;
  const [yamlError, setYamlError] = useState(
    undefined as unknown as YAMLException
  );
  const [isTouched, setIsTouched] = useState(false);
  const [isEmptyState, setIsEmptyState] = useState(!yamlData);
  const {
    flags: { navV2 },
  } = useFeatures();
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
          height={navV2 ? "calc(100vh - 526px" : "calc(100vh - 394px)"}
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
        <ButtonGroup size="sm">
          {onCancel ? <Button onClick={onCancel}>Cancel</Button> : null}
          <Button
            colorScheme="primary"
            isDisabled={disabled || isEmptyState || !!yamlError || isSubmitting}
            isLoading={isSubmitting}
            loadingText="Saving"
            onClick={handleConfirmation}
            type="submit"
            data-testid="save-yaml-btn"
            width="fit-content"
          >
            Save
          </Button>
        </ButtonGroup>
      </VStack>
      {isTouched && (isEmptyState || yamlError) && (
        <SlideFade in>
          <Box w="fit-content">
            <Divider color="gray.100" />
            <HStack mt="16px">
              <Heading as="h5" color="gray.700" size="xs">
                YAML
              </Heading>
              <Tag colorScheme="red" size="sm" variant="solid">
                Error
              </Tag>
            </HStack>
            <Box
              bg="red.50"
              border="1px solid"
              borderColor="red.300"
              color="red.300"
              mt="16px"
              borderRadius="6px"
            >
              <HStack
                alignItems="flex-start"
                margin={["14px", "17px", "14px", "17px"]}
              >
                <ErrorWarningIcon />
                {isEmptyState && (
                  <Box>
                    <Heading
                      as="h5"
                      color="red.500"
                      fontWeight="semibold"
                      size="xs"
                    >
                      Error message:
                    </Heading>
                    <Text color="gray.700" fontSize="sm" fontWeight="400">
                      YAML dataset is required
                    </Text>
                  </Box>
                )}
                {yamlError && (
                  <Box>
                    <Heading
                      as="h5"
                      color="red.500"
                      fontWeight="semibold"
                      size="xs"
                    >
                      Error message:
                    </Heading>
                    <Text color="gray.700" fontSize="sm" fontWeight="400">
                      {yamlError.message}
                    </Text>
                    <Text color="gray.700" fontSize="sm" fontWeight="400">
                      {yamlError.reason}
                    </Text>
                    <Text color="gray.700" fontSize="sm" fontWeight="400">
                      Ln <b>{yamlError.mark.line}</b>, Col{" "}
                      <b>{yamlError.mark.column}</b>, Pos{" "}
                      <b>{yamlError.mark.position}</b>
                    </Text>
                  </Box>
                )}
              </HStack>
            </Box>
          </Box>
        </SlideFade>
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
                  <>
                    <Text color="complimentary.500" as="span" fontWeight="bold">
                      {key}
                    </Text>
                    {isLast ? "." : ", "}
                  </>
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
