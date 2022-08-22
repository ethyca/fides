import {
  Box,
  Divider,
  Heading,
  HStack,
  Tag,
  Text,
  VStack,
} from "@fidesui/react";
import { ErrorWarningIcon, GreenCheckCircleIcon } from "common/Icon";
import { capitalize, formatDate } from "common/utils";
import { ConnectionOption } from "connection-type/types";
import React from "react";

type TestConnectionProps = {
  connectionOption: ConnectionOption;
  response: any;
};

const ConfigureConnector: React.FC<TestConnectionProps> = ({
  connectionOption,
  response,
}) => (
  <>
    <Divider color="gray.100" />
    <VStack align="flex-start" mt="16px">
      {response.data?.test_status === "succeeded" && (
        <>
          <HStack>
            <Heading as="h5" color="gray.700" size="xs">
              Successfully connected to{" "}
              {capitalize(connectionOption.identifier)}
            </Heading>
            <Tag colorScheme="green" size="sm" variant="solid">
              Success
            </Tag>
          </HStack>
          <Text color="gray.500" fontSize="sm" mt="12px !important">
            {formatDate(response.fulfilledTimeStamp)}
          </Text>
          <Box
            bg="green.100"
            border="1px solid"
            borderColor="green.300"
            color="green.700"
            mt="16px"
            borderRadius="6px"
          >
            <HStack
              alignItems="flex-start"
              margin={["14px", "17px", "14px", "17px"]}
            >
              <GreenCheckCircleIcon />
              <Box>
                <Heading
                  as="h5"
                  color="green.500"
                  fontWeight="semibold"
                  size="xs"
                >
                  Success message:
                </Heading>
                <Text color="gray.700" fontSize="sm" fontWeight="400">
                  {response.data.msg}
                </Text>
              </Box>
            </HStack>
          </Box>
        </>
      )}
      {response.data?.test_status === "failed" && (
        <>
          <HStack>
            <Heading as="h5" color="gray.700" size="xs">
              Output error to {capitalize(connectionOption.identifier)}
            </Heading>
            <Tag colorScheme="red" size="sm" variant="solid">
              Error
            </Tag>
          </HStack>
          <Text color="gray.500" fontSize="sm" mt="12px !important">
            {formatDate(response.fulfilledTimeStamp)}
          </Text>
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
                  {response.data.failure_reason}
                </Text>
                <Text color="gray.700" fontSize="sm" fontWeight="400">
                  {response.data.msg}
                </Text>
              </Box>
            </HStack>
          </Box>
        </>
      )}
    </VStack>
  </>
);

export default ConfigureConnector;
