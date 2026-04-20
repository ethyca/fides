"use client";

import {
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraHeading as Heading,
  ChakraStack as Stack,
  ChakraText as Text,
} from "fidesui";

import {
  METRIC_COLUMNS,
  REQUEST_TYPE_LABELS,
} from "~/features/privacy-request-metrics/constants";
import type { RequestTypeMetrics } from "~/features/privacy-request-metrics/types";
import { useGetPrivacyRequestMetrics } from "~/features/privacy-request-metrics/useGetPrivacyRequestMetrics";

function formatValue(value: number | null, key: string): string {
  if (value === null) {
    return "N/A";
  }
  if (key === "median_days_to_respond" || key === "mean_days_to_respond") {
    return String(value);
  }
  return value.toLocaleString();
}

export const PrivacyRequestMetrics = () => {
  const { data, isLoading } = useGetPrivacyRequestMetrics();

  if (isLoading) {
    return null;
  }

  const requestTypes = Object.entries(data.request_types);

  return (
    <Stack align="center" py={["6", "16"]} px={5} spacing={10}>
      <Stack align="center" spacing={3} w="100%" maxWidth={960}>
        <Heading as="h1" fontSize={["2xl", "3xl"]} fontWeight="semibold">
          Privacy request metrics
        </Heading>
        <Text color="gray.600" fontSize="sm">
          Reporting period: {data.reporting_period}
        </Text>
      </Stack>

      <Box w="100%" maxWidth={960} overflowX="auto">
        <Box
          as="table"
          w="100%"
          fontSize={["xs", "sm"]}
          style={{ borderCollapse: "collapse" }}
        >
          <Box as="thead">
            <Box as="tr" borderBottomWidth="2px" borderColor="gray.200">
              <Box
                as="th"
                textAlign="left"
                py={3}
                px={3}
                fontWeight="semibold"
                color="gray.800"
              >
                Request type
              </Box>
              {METRIC_COLUMNS.map((col) => (
                <Box
                  key={col.key}
                  as="th"
                  textAlign="right"
                  py={3}
                  px={3}
                  fontWeight="semibold"
                  color="gray.800"
                >
                  {col.label}
                </Box>
              ))}
            </Box>
          </Box>
          <Box as="tbody">
            {requestTypes.map(([typeKey, metrics]) => (
              <Box
                key={typeKey}
                as="tr"
                borderBottomWidth="1px"
                borderColor="gray.100"
                _hover={{ bg: "gray.50" }}
              >
                <Box as="td" py={3} px={3} fontWeight="medium" color="gray.800">
                  {REQUEST_TYPE_LABELS[typeKey] ?? typeKey}
                </Box>
                {METRIC_COLUMNS.map((col) => (
                  <Box
                    key={col.key}
                    as="td"
                    textAlign="right"
                    py={3}
                    px={3}
                    color="gray.700"
                  >
                    {formatValue(
                      metrics[col.key as keyof RequestTypeMetrics],
                      col.key,
                    )}
                  </Box>
                ))}
              </Box>
            ))}
          </Box>
        </Box>
      </Box>

      <Flex w="100%" maxWidth={960} justifyContent="center">
        <Text color="gray.500" fontSize="xs" textAlign="center">
          Disclosed pursuant to the California Consumer Privacy Act (CCPA) and
          California Privacy Rights Act (CPRA), Cal. Code Regs. tit. 11, &sect;
          7102.
        </Text>
      </Flex>
    </Stack>
  );
};
