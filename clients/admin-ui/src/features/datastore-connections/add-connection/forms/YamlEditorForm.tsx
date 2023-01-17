import { Button, ButtonGroup, Divider, Flex, VStack } from "@fidesui/react";
import { useAlert } from "common/hooks/useAlert";
import { Dataset } from "datastore-connections/types";
import yaml, { YAMLException } from "js-yaml";
import { useRouter } from "next/router";
import React, { useRef, useState } from "react";
import { DATASTORE_CONNECTION_ROUTE } from "src/constants";

import { useFeatures } from "~/features/common/features";
import { Editor, isYamlException } from "~/features/common/yaml/helpers";
import YamlError from "~/features/common/yaml/YamlError";

type YamlEditorFormProps = {
  data: Dataset[];
  isSubmitting: boolean;
  onSubmit: (value: any) => void;
};

const YamlEditorForm: React.FC<YamlEditorFormProps> = ({
  data = [],
  isSubmitting = false,
  onSubmit,
}) => {
  const monacoRef = useRef(null);
  const router = useRouter();
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

  const handleCancel = () => {
    router.push(DATASTORE_CONNECTION_ROUTE);
  };

  const handleMount = (editor: any) => {
    monacoRef.current = editor;
    (monacoRef.current as any).focus();
  };

  const handleSubmit = () => {
    const value = (monacoRef.current as any).getValue();
    const yamlDoc = yaml.load(value, { json: true });
    onSubmit(yamlDoc);
  };

  return (
    <Flex gap="97px">
      <VStack align="stretch" w="75%">
        <Divider color="gray.100" />
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
          }}
          theme="light"
        />
        <Divider color="gray.100" />
        <ButtonGroup
          mt="24px !important"
          size="sm"
          spacing="8px"
          variant="outline"
        >
          <Button onClick={handleCancel} variant="outline">
            Cancel
          </Button>
          <Button
            bg="primary.800"
            color="white"
            isDisabled={isEmptyState || !!yamlError || isSubmitting}
            isLoading={isSubmitting}
            loadingText="Saving Yaml system"
            onClick={handleSubmit}
            size="sm"
            variant="solid"
            type="submit"
            _active={{ bg: "primary.500" }}
            _disabled={{ opacity: "inherit" }}
            _hover={{ bg: "primary.400" }}
          >
            Save Yaml system
          </Button>
        </ButtonGroup>
      </VStack>
      {isTouched && (isEmptyState || yamlError) && (
        <YamlError isEmptyState={isEmptyState} yamlError={yamlError} />
      )}
    </Flex>
  );
};

export default YamlEditorForm;
