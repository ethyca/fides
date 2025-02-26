import {
  Box,
  ErrorWarningIcon,
  Heading,
  HStack,
  SlideFade,
  Tag,
  Text,
} from "fidesui";
import yaml from "js-yaml";
import * as React from "react";

type YamlErrorProps = {
  isEmptyState: boolean;
  yamlError?: yaml.YAMLException;
};

const YamlError = ({ isEmptyState, yamlError }: YamlErrorProps) => (
  <SlideFade in>
    <Box w="fit-content" bg="white" p={3} borderRadius={3}>
      <HStack>
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
              <Heading as="h5" color="red.500" fontWeight="semibold" size="xs">
                Error message:
              </Heading>
              <Text color="gray.700" fontSize="sm" fontWeight="400">
                Yaml system is required
              </Text>
            </Box>
          )}
          {yamlError && (
            <Box>
              <Heading as="h5" color="red.500" fontWeight="semibold" size="xs">
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
);

export default YamlError;
